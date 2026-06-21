const API_URL = "https://script.google.com/macros/s/AKfycbyWGbGYqjL-OBgkWvbo2nOF8NO4KL3251WJJD51OzrbgtF-62lfj2_ev4z4I55Sjy1d/exec";

async function sendCreator() {
  const name = document.getElementById("creatorName").value.trim();

  if (!name) {
    document.getElementById("msg").textContent = "Name required";
    document.getElementById("msg").style.color = "red";
    document.getElementById("msg").style.display = "block";
    document.getElementById("creatorName").focus();
    return;
  }

  document.getElementById("msg").textContent = "Waiting...";
  document.getElementById("msg").style.color = "blue";
  document.getElementById("msg").style.display = "block";

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "text/plain;charset=utf-8"
      },
      body: JSON.stringify({ name })
    });

    const data = await res.json();

    if (data.success) {
      msg(name + " has been saved!", "green");
      document.getElementById("creatorName").value = "";
    } else {
      if (data.reason === "duplicate") {
        msg(name + " is already in the database.", "red");
      } else if (data.reason === "invalid_name") {
        msg(name + " is not a valid creator name. Please check the name and try again.", "red");
      } else if (data.reason === "too_many_requests") {
        msg("Too many requests. Please try again later.", "red");
      } else {
        msg("Error: " + data.reason, "red");
      }
      console.log("Error:", data.reason);
    }

  } catch (err) {
    msg("Error: " + err, "red");
    console.error("Unexpected error:", err);
  }
}

function msg(message, color) {
  const msgElement = document.getElementById("msg");
  msgElement.textContent = message;
  msgElement.style.color = color;
  msgElement.style.display = "block";
  document.getElementById("creatorName").focus();
}

document.getElementById("submit-button").addEventListener("click", sendCreator);