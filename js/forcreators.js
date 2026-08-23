import { getDB, queryAll } from "./db.js";
import { initI18n, t } from "./i18n.js";

await initI18n();

const API_URL = "https://script.google.com/macros/s/AKfycbyWGbGYqjL-OBgkWvbo2nOF8NO4KL3251WJJD51OzrbgtF-62lfj2_ev4z4I55Sjy1d/exec";

const CREATOR_REGEX = /^[a-z0-9]([a-z0-9-]{0,48}[a-z0-9])?$/;

let cooldownEnd = 0;
let cooldownTimer = null;

function setMsg(message, color) {
  const el = document.getElementById("msg");
  el.textContent = message;
  el.style.color = color;
  el.style.display = "block";
}

function startCooldown() {
  const DURATION = 10;
  const btn = document.getElementById("submit-button");
  cooldownEnd = Date.now() + DURATION * 1000;
  btn.disabled = true;

  cooldownTimer = setInterval(() => {
    const remaining = Math.ceil((cooldownEnd - Date.now()) / 1000);
    if (remaining <= 0) {
      clearInterval(cooldownTimer);
      cooldownTimer = null;
      btn.disabled = false;
      btn.textContent = t("forcreators.button");
    } else {
      btn.textContent = t("forcreators.wait", { seconds: remaining });
    }
  }, 200);
}

async function sendCreator() {

  if (Date.now() < cooldownEnd) {
    return;
  }

  const name = document.getElementById("creatorName").value.trim().toLowerCase();

  if (!name) {
    setMsg(t("forcreators.empty"), "red");
    document.getElementById("creatorName").focus();
    return;
  }

  if (!CREATOR_REGEX.test(name)) {
    setMsg(t("forcreators.invalid", { name: name }), "red");
    document.getElementById("creatorName").focus();
    return;
  }

  const db = await getDB()
  const scripts = queryAll(db, `
    SELECT name, creator, thumbnail
    FROM scripts
    WHERE creator = ?
    ORDER BY name
    LIMIT 1
  `, [name]);
  if (scripts.length > 0) {
    setMsg(t("forcreators.duplicate", { name: name }), "red");
    document.getElementById("creatorName").focus();
    return;
  }

  const cfToken = window.turnstile?.getResponse();
  if (!cfToken) {
    setMsg(t("forcreators.captcha"), "red");
    return;
  }

  setMsg(t("forcreators.sending"), "blue");
  document.getElementById("submit-button").disabled = true;

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify({ name, cfToken })
    });

    const data = await res.json();

    window.turnstile?.reset();

    document.getElementById("submit-button").disabled = false;

    if (data.success) {
      setMsg(t("forcreators.success", { name: name }), "green");
      document.getElementById("creatorName").value = "";
      document.getElementById("creatorName").focus();
    } else {
      startCooldown()

      switch (data.reason) {
        case "duplicate":
          setMsg(t("forcreators.duplicate", { name: name }), "red");
          document.getElementById("creatorName").focus();
          break;
        case "invalid_name":
          setMsg(t("forcreators.invalid", { name: name }), "red");
          break;
        case "captcha_failed":
          setMsg(t("forcreators.captcha"), "red");
          break;
        case "too_many_requests":
          setMsg(t("forcreators.too_many_requests"), "red");
          document.getElementById("creatorName").focus();
          break;
        case "numworks_user_not_found":
          setMsg(t("forcreators.not_found", { name: name }), "red");
          document.getElementById("creatorName").focus();
          break;
        default:
          setMsg(t("forcreators.error", { reason: data.reason }), "red");
      }
    }

  } catch (err) {
    window.turnstile?.reset();
    document.getElementById("submit-button").disabled = false;
    setMsg(t("forcreators.network-error"), "red");
    console.error("Unexpected error:", err);
  }
}

document.getElementById("submit-button").addEventListener("click", sendCreator);

document.getElementById("creatorName").addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendCreator();
});