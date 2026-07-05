import { getDB, queryAll } from "./db.js";
import { buildScriptCard } from "./utils.js";

async function loadScripts() {
  const grid = document.getElementById("scripts-grid");
  grid.replaceChildren();

  const db = await getDB();

  const scripts = queryAll(db, `
    SELECT name, creator, thumbnail
    FROM scripts
    ORDER BY RANDOM()
    LIMIT 12
  `);

  for (const script of scripts) {
    grid.appendChild(buildScriptCard(script));
  }
}

document.addEventListener("DOMContentLoaded", loadScripts);