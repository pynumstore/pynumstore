import { getDB, queryAll } from "./db.js";
import { buildScriptCard } from "./utils.js";
import { initI18n, t } from "./i18n.js";

await initI18n();

const VALID_ID = /^[a-z0-9]([a-z0-9-]{0,48}[a-z0-9])?$/;

function getSortOptions() {
  return [
    { value: "name-asc",   label: t("search.az")       },
    { value: "name-desc",  label: t("search.za")       },
    { value: "date-desc",  label: t("search.newest")   },
    { value: "date-asc",   label: t("search.oldest")   },
    { value: "size-desc",  label: t("search.largest")  },
    { value: "size-asc",   label: t("search.smallest") },
  ];
}

let allScripts = [];
let currentCreator = null;
let currentSort = "name-asc";

async function loadCreatorPage() {
  const params  = new URLSearchParams(window.location.search);
  const creator = params.get("name");
  const initialSort = params.get("sort") ?? "name-asc";
  currentSort = initialSort;

  if (!creator || !VALID_ID.test(creator)) {
    document.title = t("creator.titleDefault");
    document.getElementById("creator-name").textContent = t("creator.invalid");
    return;
  }

  currentCreator = creator;
  document.title = t("creator.titleName", { name: creator });
  document.getElementById("creator-name").textContent = creator;

  buildSortButtons(initialSort);

  const db = await getDB();
  allScripts = queryAll(db, `
    SELECT name, creator, thumbnail, updated_at, size
    FROM scripts
    WHERE creator = ?
  `, [creator]);

  updateScriptCount();
  renderScripts(initialSort);

  document.addEventListener("i18n:changed", () => {
    document.title = t("creator.titleName", { name: currentCreator });
    buildSortButtons(currentSort);
    updateScriptCount();
  });
}

function buildSortButtons(activeValue) {
  const sortBar = document.getElementById("sort-buttons");
  sortBar.replaceChildren();
  getSortOptions().forEach(({ value, label }) => {
    const btn = document.createElement("button");
    btn.className   = "sort-btn" + (value === activeValue ? " active" : "");
    btn.dataset.sort = value;
    btn.textContent  = label;
    btn.addEventListener("click", () => setSort(value));
    sortBar.appendChild(btn);
  });
}

function updateScriptCount() {
  const count = allScripts.length;
  document.getElementById("script-count").textContent =
    `${count.toLocaleString()} ${t("search.script").toLowerCase()}${count !== 1 ? "s" : ""}`;
}

function setSort(order) {
  currentSort = order;
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
    case "date-desc": return sorted.sort((a, b) => (b.updated_at ?? "").localeCompare(a.updated_at ?? ""));
    case "date-asc":  return sorted.sort((a, b) => (a.updated_at ?? "").localeCompare(b.updated_at ?? ""));
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

loadCreatorPage();