import Fuse from "https://cdn.jsdelivr.net/npm/fuse.js@6.6.2/dist/fuse.esm.js";
import { buildScriptCard } from "./utils.js";

let fuse;
let allScripts = [];
const metadataCache = {};

async function initSearch() {
  const res = await fetch("data/scripts_index.json");
  allScripts = await res.json();

  fuse = new Fuse(allScripts, {
    keys: ["name", "creator"],
    threshold: 0.2,
    ignoreLocation: true
  });

  const params = new URLSearchParams(window.location.search);
  const query = params.get("q") || "";

  if (query) {
    await search(query);
  } else {
    await search("");
  }
}

async function search(query) {
  let search;

  if (query && query.trim() !== "") {
    search = fuse.search(query).map(r => r.item);
  } else {
    search = allScripts;
  }

  search = shuffle(search).slice(0, 21);

  await render(search, query);
}

async function render(list, query) {
  const grid = document.getElementById("results");
  grid.replaceChildren();

  for (const script of list) {
    const key = `${script.creator}/${script.name}`;

    if (!metadataCache[key]) {
      const res = await fetch(
        `data/${encodeURIComponent(script.creator)}/${encodeURIComponent(script.name)}/metadata.json`
      );
      metadataCache[key] = await res.json();
    }

    const meta = metadataCache[key];
    grid.appendChild(buildScriptCard(script, meta));
  }

  document.title = query
    ? `PyNumStore - Search for "${query}"`
    : `PyNumStore - Search`;

  const title = document.getElementById("results-title");
  if (title) {
    title.textContent = query
      ? `Results for "${query}" (${list.length})`
      : `All scripts`;
  }
}

function shuffle(array) {
  const arr = [...array];

  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }

  return arr;
}

document.addEventListener("DOMContentLoaded", initSearch);

document.getElementById("search-button").addEventListener("click", () => {
  const query = document.getElementById("search-input").value;
  search(query);
});

document.getElementById("search-input").addEventListener("keypress", (event) => {
  if (event.key === "Enter") {
    const query = document.getElementById("search-input").value;
    search(query);
  }
});