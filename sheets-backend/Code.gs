/**
 * Kleine REST-API vor GENAU EINEM Google Sheet.
 *
 * Wichtig: Dieses Skript ist bewusst für nur eine Person gedacht. Für
 * Schwester und Frau braucht ihr zwei komplett getrennte Google Sheets,
 * jedes mit einer eigenen Kopie dieses Skripts und einer eigenen
 * Bereitstellung (eigene URL, eigenes SECRET). Siehe SETUP.md.
 */

const SHEET_NAME = "interactions";
const SECRET = "CHANGE_ME_TO_A_LONG_RANDOM_STRING";

function doGet(e) {
  if (e.parameter.token !== SECRET) {
    return jsonResponse_({ error: "unauthorized" });
  }
  const sheet = getSheet_();
  const rows = sheet.getDataRange().getValues();
  const header = rows.shift();
  const result = {};

  rows.forEach(function (row) {
    const record = {};
    header.forEach(function (key, i) { record[key] = row[i]; });
    result[record.job_id] = {
      liked: record.liked === true || record.liked === "true",
      hidden: record.hidden === true || record.hidden === "true",
    };
  });

  return jsonResponse_(result);
}

function doPost(e) {
  const body = JSON.parse(e.postData.contents);
  if (body.token !== SECRET) {
    return jsonResponse_({ error: "unauthorized" });
  }

  const sheet = getSheet_();
  const data = sheet.getDataRange().getValues();
  const header = data[0];
  const jobCol = header.indexOf("job_id");

  let rowIndex = -1;
  for (let i = 1; i < data.length; i++) {
    if (data[i][jobCol] === body.job_id) {
      rowIndex = i + 1; // 1-indexiert für getRange
      break;
    }
  }

  const rowValues = [body.job_id, !!body.liked, !!body.hidden, new Date().toISOString()];

  if (rowIndex === -1) {
    sheet.appendRow(rowValues);
  } else {
    sheet.getRange(rowIndex, 1, 1, rowValues.length).setValues([rowValues]);
  }

  return jsonResponse_({ ok: true });
}

function getSheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(["job_id", "liked", "hidden", "updated_at"]);
  }
  return sheet;
}

function jsonResponse_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
