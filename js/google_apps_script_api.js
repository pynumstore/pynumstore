function doPost(e) {

  const cache = CacheService.getScriptCache();
  const ip = e.parameter.ip || "unknown";

  if (cache.get(ip)) {
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        reason: "too_many_requests"
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  cache.put(ip, "1", 10);
  
  try {
    const data = JSON.parse(e.postData.contents);
    const name = String(data.name || "").toLowerCase();

    const result = validateAndStore(name);

    return ContentService
      .createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        error: err.toString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function validateAndStore(name) {

  if (!creatorNameIsValid(name)) {
    return {
      success: false,
      reason: "invalid_name"
    };
  }

  const sheet = SpreadsheetApp
    .openById("******************************************************")
    .getSheetByName("creators_index");

  const lastRow = sheet.getLastRow();

  let values = [];

  if (lastRow > 1) {
    values = sheet
      .getRange(1, 1, lastRow - 1, 1)
      .getValues()
      .flat()
      .map(v => String(v).toLowerCase());
  }

  if (values.includes(name)) {
    return {
      success: false,
      reason: "duplicate"
    };
  }

  sheet.appendRow([name]);

  return {
    success: true,
    reason: "saved"
  };
}

function creatorNameIsValid(name) {

  if (!name) return false;

  if (name[0] === "-" || name[name.length - 1] === "-") {
    return false;
  }

  if (name.length > 50) {
    return false;
  }

  for (const c of name) {
    const valid =
      (c >= "a" && c <= "z") ||
      (c >= "0" && c <= "9") ||
      c === "-";

    if (!valid) {
      return false;
    }
  }

  return true;
}