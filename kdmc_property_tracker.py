import json
import os
import re
from datetime import datetime, timezone

import gspread
import requests
from bs4 import BeautifulSoup
from google.oauth2.service_account import Credentials


BASE_URL = "https://kdmc.gov.in/kdmc/PropertyBillPayment.html"
SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Sheet1")
PROPERTY_COLUMN = os.getenv("PROPERTY_COLUMN", "Property Number")

OUTPUT_COLUMNS = [
    "Owner Name",
    "Address",
    "Location",
    "Current Tax",
    "Current Penalty",
    "Rebate",
    "Total Payable",
    "Payment Amount",
    "Last Checked",
    "Status",
]


def get_required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def open_sheet():
    service_account_json = get_required_env("GOOGLE_SERVICE_ACCOUNT_JSON")
    sheet_id = get_required_env("GOOGLE_SHEET_ID")
    credentials_info = json.loads(service_account_json)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_info(credentials_info, scopes=scopes)
    client = gspread.authorize(credentials)
    return client.open_by_key(sheet_id).worksheet(SHEET_NAME)


def ensure_headers(worksheet):
    headers = worksheet.row_values(1)
    if not headers:
        headers = [PROPERTY_COLUMN]
        worksheet.update("A1", [headers])

    changed = False
    for column in [PROPERTY_COLUMN, *OUTPUT_COLUMNS]:
        if column not in headers:
            headers.append(column)
            changed = True

    if changed:
        worksheet.update("1:1", [headers])

    return {header: index + 1 for index, header in enumerate(headers)}


def first_value(soup, selector):
    element = soup.select_one(selector)
    if not element:
        return ""
    if element.name == "textarea":
        return clean_text(element.get_text())
    return clean_text(element.get("value", ""))


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def extract_table_numbers(soup):
    current_tax = ""
    current_penalty = ""
    rebate = ""

    for row in soup.select("tr"):
        cells = [clean_text(cell.get_text()) for cell in row.select("th, td")]
        if not cells:
            continue
        if cells[0].lower() == "total" and len(cells) >= 3:
            current_tax = cells[2]
        row_text = " ".join(cells)
        if "चालू व्याज" in row_text or "Current Penalty" in row_text:
            numbers = re.findall(r"\d+(?:\.\d+)?", row_text)
            if numbers:
                current_penalty = numbers[0]
        if "सूट" in row_text or "Rebate" in row_text:
            numbers = re.findall(r"\d+(?:\.\d+)?", row_text)
            if len(numbers) >= 2:
                rebate = numbers[1]
            elif numbers:
                rebate = numbers[0]

    rebate_element = soup.select_one("#rebateId")
    if rebate_element:
        rebate = clean_text(rebate_element.get_text())

    return current_tax, current_penalty, rebate


def fetch_property_details(property_number):
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; KDMCPropertyTracker/1.0)",
        "Referer": BASE_URL,
    }

    page = session.get(BASE_URL, headers=headers, timeout=30)
    page.raise_for_status()
    page_soup = BeautifulSoup(page.text, "html.parser")
    csrf_input = page_soup.select_one('input[name="_csrf"]')
    csrf_meta = page_soup.select_one('meta[name="_csrf"]')
    csrf = ""
    if csrf_input:
        csrf = csrf_input.get("value", "")
    elif csrf_meta:
        csrf = csrf_meta.get("content", "")
    if not csrf:
        raise RuntimeError("Could not find KDMC CSRF token")

    post_headers = {
        **headers,
        "X-CSRF-TOKEN": csrf,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    data = {
        "billingMethod": "",
        "propBillPaymentDto.assNo": property_number,
        "propBillPaymentDto.flatNo": "",
        "_csrf": csrf,
    }
    response = session.post(
        f"{BASE_URL}?getBillPaymentDetail",
        headers=post_headers,
        data=data,
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    if not soup.select_one("#PropertyBillPayment"):
        message = clean_text(soup.get_text(" "))[:300]
        raise RuntimeError(message or "KDMC did not return bill details")

    current_tax, current_penalty, rebate = extract_table_numbers(soup)
    return {
        "Owner Name": first_value(soup, "#primaryOwnerName"),
        "Address": first_value(soup, "#address"),
        "Location": first_value(soup, "#location"),
        "Current Tax": current_tax,
        "Current Penalty": current_penalty,
        "Rebate": rebate,
        "Total Payable": first_value(soup, "#totalPayable"),
        "Payment Amount": first_value(soup, "#payAmount"),
        "Last Checked": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "Status": "OK",
    }


def update_row(worksheet, row_number, columns, values):
    updates = []
    for column_name, value in values.items():
        column_number = columns[column_name]
        updates.append({"range": gspread.utils.rowcol_to_a1(row_number, column_number), "values": [[value]]})
    worksheet.batch_update(updates, value_input_option="USER_ENTERED")


def main():
    worksheet = open_sheet()
    columns = ensure_headers(worksheet)
    records = worksheet.get_all_records()

    for offset, record in enumerate(records, start=2):
        property_number = clean_text(record.get(PROPERTY_COLUMN, ""))
        if not property_number:
            continue

        try:
            print(f"Checking {property_number}")
            details = fetch_property_details(property_number)
        except Exception as exc:
            details = {
                "Last Checked": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "Status": f"ERROR: {exc}",
            }
        update_row(worksheet, offset, columns, details)


if __name__ == "__main__":
    main()
