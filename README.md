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

## Recommended Setup: Google Apps Script, No Service Account Key

Use this if Google shows `Service account key creation is disabled`.

1. Open your Google Sheet.
2. Go to `Extensions > Apps Script`.
3. Paste the contents of `google_apps_script.gs`.
4. Change this line to a long random secret:

```js
const TOKEN = 'CHANGE_THIS_TO_A_LONG_RANDOM_SECRET';
```

5. If your tab is not named `Sheet1`, update:

```js
const SHEET_NAME = 'Sheet1';
```

6. Click `Deploy > New deployment`.
7. Select type `Web app`.
8. Set `Execute as` to `Me`.
9. Set `Who has access` to `Anyone`.
10. Click `Deploy` and authorize access.
11. Copy the Web App URL.

Add these under `Settings > Secrets and variables > Actions > New repository secret`:

```text
APPS_SCRIPT_WEB_APP_URL
APPS_SCRIPT_TOKEN
```

`APPS_SCRIPT_TOKEN` must match the `TOKEN` value in Apps Script.

## Alternative Setup: Service Account JSON

Use this only if your Google account allows service account key creation.

## Required GitHub Secrets For Service Account Mode

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
