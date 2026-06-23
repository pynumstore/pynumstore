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
      btn.textContent = "Submit";
    } else {
      btn.textContent = `Wait ${remaining}s`;
    }
  }, 200);
}

async function sendCreator() {

  if (Date.now() < cooldownEnd) {
    return;
  }

  const name = document.getElementById("creatorName").value.trim().toLowerCase();

  if (!name) {
    setMsg("Please enter a creator name.", "red");
    document.getElementById("creatorName").focus();
    return;
  }

  if (!CREATOR_REGEX.test(name)) {
    setMsg(
      `"${name}" is not a valid creator name. Only lowercase letters, digits and hyphens are allowed, and it cannot start or end with a hyphen.`,
      "red"
    );
    document.getElementById("creatorName").focus();
    return;
  }

  const cfToken = window.turnstile?.getResponse();
  if (!cfToken) {
    setMsg("Please complete the security check.", "red");
    return;
  }

  setMsg("Sending...", "blue");
  document.getElementById("submit-button").disabled = true;

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify({ name, cfToken })
    });

    const data = await res.json();

    window.turnstile?.reset();

    if (data.success) {
      setMsg(`"${name}" has been added to the database!`, "green");
      document.getElementById("creatorName").value = "";
    } else {
      startCooldown()
      document.getElementById("submit-button").disabled = false;

      switch (data.reason) {
        case "duplicate":
          setMsg(`"${name}" is already in the database.`, "red");
          break;
        case "invalid_name":
          setMsg(`"${name}" is not a valid creator name.`, "red");
          break;
        case "captcha_failed":
          setMsg("Security check failed. Please try again.", "red");
          break;
        case "too_many_requests":
          setMsg("Too many requests. Please try again later.", "red");
          break;
        case "numworks_user_not_found":
          setMsg("This creator doesn't exists the NumWorks website.", "red");
          break;
        default:
          setMsg(`Error: ${data.reason}`, "red");
      }
    }

  } catch (err) {
    window.turnstile?.reset();
    document.getElementById("submit-button").disabled = false;
    setMsg("Network error. Please check your connection and try again.", "red");
    console.error("Unexpected error:", err);
  }
}

document.getElementById("submit-button").addEventListener("click", sendCreator);

document.getElementById("creatorName").addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendCreator();
});