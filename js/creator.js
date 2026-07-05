import { getDB, queryAll } from "./db.js";
import { buildScriptCard } from "./utils.js";

const VALID_ID = /^[a-z0-9]([a-z0-9-]{0,48}[a-z0-9])?$/;

async function loadCreatorPage() {
  const params  = new URLSearchParams(window.location.search);
  const creator = params.get("name");

  if (!creator || !VALID_ID.test(creator)) {
    document.getElementById("creator-name").textContent = "Invalid creator";
    return;
  }

  document.title = `PyNumStore - ${creator}`;
  document.getElementById("creator-name").textContent = creator;

  const db      = await getDB();
  const scripts = queryAll(db, `
    SELECT name, creator, thumbnail
    FROM scripts
    WHERE creator = ?
    ORDER BY name
  `, [creator]);

  const grid = document.getElementById("scripts-grid");
  grid.replaceChildren();

  for (const script of scripts) {
    grid.appendChild(buildScriptCard(script));
  }
}

document.addEventListener("DOMContentLoaded", loadCreatorPage);