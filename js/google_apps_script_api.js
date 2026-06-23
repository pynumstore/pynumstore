const TURNSTILE_SECRET_KEY = PropertiesService
  .getScriptProperties()
  .getProperty("TURNSTILE_SECRET_KEY");

const SHEET_ID = PropertiesService
  .getScriptProperties()
  .getProperty("SHEET_ID");

const CREATOR_REGEX = /^[a-z0-9]([a-z0-9-]{0,48}[a-z0-9])?$/;

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const name = String(data.name || "").toLowerCase().trim();
    const cfToken = String(data.cfToken || "");
    const vTurnstile = verifyTurnstile(cfToken);

    if (!vTurnstile[0]) {
      return response({ success: false, reason: "captcha_failed: " + vTurnstile[1] });
    }

    const cache = CacheService.getScriptCache();
    const cacheKey = "cooldown_" + name;
    if (cache.get(cacheKey)) {
      return response({ success: false, reason: "too_many_requests" });
    }
    cache.put(cacheKey, "1", 30);

    if (!CREATOR_REGEX.test(name)) {
      return response({ success: false, reason: "invalid_name" });
    }

    if (!numworksUserExists(name)) {
      return response({
        success: false,
        reason: "numworks_user_not_found"
      });
    }

    return response(validateAndStore(name));

  } catch (err) {
    return response({ success: false, reason: err.toString() });
  }
}

function verifyTurnstile(token) {
  if (!token) return [false, "missing_token"];

  try {
    const res = UrlFetchApp.fetch(
      "https://challenges.cloudflare.com/turnstile/v0/siteverify",
      {
        method: "post",
        payload: {
          secret: TURNSTILE_SECRET_KEY,
          response: token
        },
        muteHttpExceptions: true
      }
    );

    const code = res.getResponseCode();
    const text = res.getContentText();

    if (code !== 200) {
      return [false, `http_${code}: ${text}`];
    }

    const result = JSON.parse(text);

    return result.success
      ? [true, ""]
      : [false, JSON.stringify(result["error-codes"] || [])];

  } catch (err) {
    return [false, String(err)];
  }
}

function validateAndStore(name) {
  const sheet = SpreadsheetApp
    .openById(SHEET_ID)
    .getSheetByName("creators_index");

  const lastRow = sheet.getLastRow();

  const existing = lastRow > 0
    ? sheet.getRange(1, 1, lastRow, 1).getValues().flat().map(v => String(v).toLowerCase().trim())
    : [];

  if (existing.includes(name)) {
    return { success: false, reason: "duplicate" };
  }

  sheet.appendRow([name]);
  return { success: true };
}

function numworksUserExists(name) {
  try {
    const res = UrlFetchApp.fetch(
      "https://my.numworks.com/python/" + encodeURIComponent(name),
      {
        method: "get",
        muteHttpExceptions: true
      }
    );

    return res.getResponseCode() === 200;
  } catch (err) {
    return false;
  }
}

function response(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}