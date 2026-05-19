# KDMC Property Tracker

This repo runs online with GitHub Actions. It reads KDMC property numbers from a Google Sheet, checks the KDMC property bill page, and updates the same sheet.

## Google Sheet

Create a sheet with this header in row 1:

```text
Property Number
```

Add one property number per row. The workflow adds and updates these columns automatically:

```text
Owner Name, Address, Location, Current Tax, Current Penalty, Rebate, Total Payable, Payment Amount, Last Checked, Status
```

## Required GitHub Secrets

Add these under `Settings > Secrets and variables > Actions > New repository secret`:

```text
GOOGLE_SERVICE_ACCOUNT_JSON
GOOGLE_SHEET_ID
```

`GOOGLE_SERVICE_ACCOUNT_JSON` is the full JSON content downloaded from Google Cloud. Do not commit it to this repo.

`GOOGLE_SHEET_ID` is the long ID in your Google Sheet URL:

```text
https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit
```

## Optional Variables

Add these under `Settings > Secrets and variables > Actions > Variables` only if needed:

```text
GOOGLE_SHEET_NAME=Sheet1
PROPERTY_COLUMN=Property Number
```

## Run Online

Go to `Actions > Update KDMC property bills > Run workflow`.

The workflow also runs daily at `08:00 IST`.
