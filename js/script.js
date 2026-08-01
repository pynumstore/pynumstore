import { getDB, queryOne } from "./db.js";

const VALID_CREATOR = /^[a-z0-9]([a-z0-9-]{0,48}[a-z0-9])?$/;
const VALID_NAME    = /^[a-z_][a-z0-9_]{0,49}$/;

async function loadScriptPage() {
  const params  = new URLSearchParams(window.location.search);
  const creator = params.get("creator");
  const name    = params.get("name");

  if (!creator || !name || !VALID_CREATOR.test(creator) || !VALID_NAME.test(name)) {
    document.querySelector(".name").textContent = "Script not found.";
    return;
  }

  const db     = await getDB();
  const script = queryOne(db, `
    SELECT * FROM scripts
    WHERE creator = ? AND name = ?
  `, [creator, name]);

  if (!script) {
    document.querySelector(".name").textContent = "Script not found.";
    return;
  }

  document.title = `PyNumStore - ${script.name}`;
  document.querySelector(".name").textContent = script.name;

  const creatorEl   = document.querySelector(".creator");
  creatorEl.textContent = "By ";
  const creatorLink = document.createElement("a");
  creatorLink.href      = `creator.html?name=${encodeURIComponent(creator)}`;
  creatorLink.textContent = creator;
  creatorEl.appendChild(creatorLink);
  const date = new Date(script.updated_at + "T00:00:00");
  document.querySelector(".updated-at").textContent =
    "Last updated: " + date.toLocaleDateString("en-US", {
      year: "numeric", month: "long", day: "numeric"
    });
  document.querySelector(".size").textContent = formatSize(script.size);

  document.getElementById("numworks-link").href =
    `https://my.numworks.com/python/${encodeURIComponent(creator)}/${encodeURIComponent(name)}/`;

  document.getElementById("script-image").src = script.thumbnail;

  if (script.description) {
    const descSection = document.querySelector(".description");
    descSection.replaceChildren();

    const h2 = document.createElement("h2");
    h2.textContent = "Description:";

    const divider = document.createElement("div");
    divider.className = "divider";

    const div = document.createElement("div");
    div.className = "description-text";
    div.innerHTML = script.description;

    div.querySelectorAll("code").forEach(el => {
      if (el.textContent.includes("\n") && el.closest("pre") === null) {
        el.classList.add("code-block");
      }
    });

    descSection.append(h2, divider, div);
  }

  let tags = [];
  try {
    tags = script.tags ? script.tags.split(",").map(t => t.trim()).filter(Boolean) : [];
  } catch {
    tags = [];
  }

  const tagsContainer = document.querySelector(".tags");
  if (tags.length) {
    tagsContainer.replaceChildren();

    const h2 = document.createElement("h2");
    h2.textContent = "Tags:";

    const divider = document.createElement("div");
    divider.className = "divider";

    tagsContainer.append(h2, divider);

    for (const t of tags) {
      const p = document.createElement("p");
      p.textContent = `#${t}`;
      tagsContainer.appendChild(p);
    }
  }
}

function formatSize(bytes) {
    if (!bytes) return "Unknown size";
    if (bytes < 1024) return `${bytes} Bytes`;
    return `${(bytes / 1024).toFixed(2)} KB`;
}

document.addEventListener("DOMContentLoaded", loadScriptPage);