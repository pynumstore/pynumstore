import { getDB, queryAll } from "./db.js";
import { buildScriptCard } from "./utils.js";

const VALID_ID = /^[a-z0-9]([a-z0-9-]{0,48}[a-z0-9])?$/;

const SORT_OPTIONS = [
  { value: "name-asc",  label: "A → Z"       },
  { value: "name-desc", label: "Z → A"       },
  { value: "date-desc", label: "Newest first" },
  { value: "date-asc",  label: "Oldest first" },
  { value: "size-desc", label: "Largest first" },
  { value: "size-asc",  label: "Smallest first" },
];

let allScripts = [];

async function loadCreatorPage() {
  const params  = new URLSearchParams(window.location.search);
  const creator = params.get("name");
  const initialSort = params.get("sort") ?? "name-asc";

  if (!creator || !VALID_ID.test(creator)) {
    document.getElementById("creator-name").textContent = "Invalid creator";
    return;
  }

  document.title = `PyNumStore - ${creator}`;
  document.getElementById("creator-name").textContent = creator;

  const sortBar = document.getElementById("sort-buttons");
  SORT_OPTIONS.forEach(({ value, label }) => {
    const btn = document.createElement("button");
    btn.className   = "sort-btn" + (value === initialSort ? " active" : "");
    btn.dataset.sort = value;
    btn.textContent  = label;
    btn.addEventListener("click", () => setSort(value));
    sortBar.appendChild(btn);
  });

  const db = await getDB();
  allScripts = queryAll(db, `
    SELECT name, creator, thumbnail, created_at, size
    FROM scripts
    WHERE creator = ?
  `, [creator]);
  
  document.getElementById("script-count").textContent =
    `${allScripts.length.toLocaleString()} script${allScripts.length !== 1 ? "s" : ""}`;

  renderScripts(initialSort);
}

function setSort(order) {
  const url = new URL(window.location.href);
  url.searchParams.set("sort", order);
  history.replaceState(null, "", url);

  document.querySelectorAll(".sort-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.sort === order);
  });

  renderScripts(order);
}

function sortScripts(scripts, order) {
  const sorted = [...scripts];
  switch (order) {
    case "name-asc":  return sorted.sort((a, b) => a.name.localeCompare(b.name));
    case "name-desc": return sorted.sort((a, b) => b.name.localeCompare(a.name));
    case "date-desc": return sorted.sort((a, b) => (b.created_at ?? "").localeCompare(a.created_at ?? ""));
    case "date-asc":  return sorted.sort((a, b) => (a.created_at ?? "").localeCompare(b.created_at ?? ""));
    case "size-desc": return sorted.sort((a, b) => (b.size ?? 0) - (a.size ?? 0));
    case "size-asc":  return sorted.sort((a, b) => (a.size ?? 0) - (b.size ?? 0));
    default:          return sorted;
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