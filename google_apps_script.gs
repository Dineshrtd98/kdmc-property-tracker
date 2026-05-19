const TOKEN = 'CHANGE_THIS_TO_A_LONG_RANDOM_SECRET';
const SHEET_NAME = 'Sheet1';

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents || '{}');
    if (body.token !== TOKEN) {
      return json({ ok: false, error: 'Unauthorized' });
    }

    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
    if (!sheet) {
      return json({ ok: false, error: `Sheet not found: ${SHEET_NAME}` });
    }

    if (body.action === 'headers') {
      return json({ ok: true, headers: getHeaders(sheet) });
    }

    if (body.action === 'setHeaders') {
      sheet.getRange(1, 1, 1, body.headers.length).setValues([body.headers]);
      return json({ ok: true });
    }

    if (body.action === 'rows') {
      return json({ ok: true, rows: getRows(sheet) });
    }

    if (body.action === 'updateRow') {
      updateRow(sheet, body.rowNumber, body.values || {});
      return json({ ok: true });
    }

    return json({ ok: false, error: `Unknown action: ${body.action}` });
  } catch (err) {
    return json({ ok: false, error: String(err) });
  }
}

function getHeaders(sheet) {
  const lastColumn = Math.max(sheet.getLastColumn(), 1);
  return sheet.getRange(1, 1, 1, lastColumn).getValues()[0].map(String);
}

function getRows(sheet) {
  const headers = getHeaders(sheet);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];

  return sheet.getRange(2, 1, lastRow - 1, headers.length).getValues().map((row, index) => {
    const record = {};
    headers.forEach((header, columnIndex) => {
      record[header] = row[columnIndex];
    });
    record.rowNumber = index + 2;
    return record;
  });
}

function updateRow(sheet, rowNumber, valuesByColumnLetter) {
  Object.keys(valuesByColumnLetter).forEach((columnLetter) => {
    sheet.getRange(`${columnLetter}${rowNumber}`).setValue(valuesByColumnLetter[columnLetter]);
  });
}

function json(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
