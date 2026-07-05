import { getDB, queryAll } from "./db.js";
import { buildScriptCard } from "./utils.js";

let db;

async function initSearch() {
  db = await getDB();

  const params = new URLSearchParams(window.location.search);
  const query  = params.get("q") ?? "";

  if (query) document.getElementById("search-input").value = query;

  await search(query);
}

async function search(query) {
  let scripts;

  if (query && query.trim()) {
    const pattern = `%${query.trim()}%`;
    scripts = queryAll(db, `
      SELECT name, creator, thumbnail
      FROM scripts
      WHERE name             LIKE ? 
         OR creator          LIKE ?
         OR description_text LIKE ?
      ORDER BY
        CASE
          WHEN name    LIKE ? THEN 0
          WHEN creator LIKE ? THEN 1
          ELSE 2
        END,
        name
      LIMIT 21
    `, [pattern, pattern, pattern, pattern, pattern]);

  } else {
    scripts = queryAll(db, `
      SELECT name, creator, thumbnail
      FROM scripts
      ORDER BY RANDOM()
      LIMIT 21
    `);
  }

  render(scripts, query);
}

function render(scripts, query) {
  const grid = document.getElementById("results");
  grid.replaceChildren();

  for (const script of scripts) {
    grid.appendChild(buildScriptCard(script));
  }

  document.title = query
    ? `PyNumStore - Search for "${query}"`
    : `PyNumStore - Search`;

  const title = document.getElementById("results-title");
  if (title) {
    title.textContent = query
      ? `Results for "${query}" (${scripts.length})`
      : `All scripts`;
  }
}

document.addEventListener("DOMContentLoaded", initSearch);

document.getElementById("search-button").addEventListener("click", () => {
  search(document.getElementById("search-input").value);
});

document.getElementById("search-input").addEventListener("keypress", e => {
  if (e.key === "Enter") search(document.getElementById("search-input").value);
});