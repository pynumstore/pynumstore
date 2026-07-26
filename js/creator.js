import { getDB, queryAll } from "./db.js";
import { buildScriptCard } from "./utils.js";

const VALID_ID = /^[a-z0-9]([a-z0-9-]{0,48}[a-z0-9])?$/;

let allScripts = [];

async function loadCreatorPage() {
  const params  = new URLSearchParams(window.location.search);
  const creator = params.get("name");

  if (!creator || !VALID_ID.test(creator)) {
    document.getElementById("creator-name").textContent = "Invalid creator";
    return;
  }

  document.title = `PyNumStore - ${creator}`;
  document.getElementById("creator-name").textContent = creator;

  const db  = await getDB();
  allScripts = queryAll(db, `
    SELECT name, creator, thumbnail, created_at, size
    FROM scripts
    WHERE creator = ?
  `, [creator]);

  renderScripts("name-asc");

  document.getElementById("sort-select").addEventListener("change", e => {
    renderScripts(e.target.value);
  });
}

function sortScripts(scripts, order) {
  const sorted = [...scripts];
  switch (order) {
    case "name-asc":
      return sorted.sort((a, b) => a.name.localeCompare(b.name));
    case "name-desc":
      return sorted.sort((a, b) => b.name.localeCompare(a.name));
    case "date-desc":
      return sorted.sort((a, b) => (b.created_at ?? "").localeCompare(a.created_at ?? ""));
    case "date-asc":
      return sorted.sort((a, b) => (a.created_at ?? "").localeCompare(b.created_at ?? ""));
    case "size-desc":
      return sorted.sort((a, b) => (b.size ?? 0) - (a.size ?? 0));
    case "size-asc":
      return sorted.sort((a, b) => (a.size ?? 0) - (b.size ?? 0));
    default:
      return sorted;
  }
}

function renderScripts(order) {
  const grid = document.getElementById("scripts-grid");
  grid.replaceChildren();
  for (const script of sortScripts(allScripts, order)) {
    grid.appendChild(buildScriptCard(script));
  }
}

document.addEventListener("DOMContentLoaded", loadCreatorPage);