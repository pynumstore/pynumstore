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
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ name })
    });

    const data = await res.json();

    if (data.success) {
      document.getElementById("msg").textContent = name + " has been saved!";
      document.getElementById("msg").style.color = "green";
      document.getElementById("msg").style.display = "block";
      document.getElementById("creatorName").value = "";
      document.getElementById("creatorName").focus();
    } else {
      if (data.reason === "duplicate") {
        document.getElementById("msg").textContent = name + " is already in the database.";
      } else if (data.reason === "invalid_name") {
        document.getElementById("msg").textContent = name + " is not a valid creator name. Please check the name and try again.";
      } else if (data.reason === "too_many_requests") {
        document.getElementById("msg").textContent = "Too many requests. Please try again later.";
      } else {
        document.getElementById("msg").textContent = "Error: " + data.reason;
      }
      document.getElementById("msg").style.color = "red";
      document.getElementById("msg").style.display = "block";
      document.getElementById("creatorName").focus();
      console.log("Error:", data.reason);
    }

  } catch (err) {
    document.getElementById("msg").textContent = "Error: " + err;
    document.getElementById("msg").style.color = "red";
    document.getElementById("msg").style.display = "block";
    document.getElementById("creatorName").focus();
    console.error("Unexpected error:", err);
  }
}