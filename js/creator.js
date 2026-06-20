import { buildScriptCard } from "./utils.js";

const VALID_ID = /^[a-z0-9-]{1,50}$/;

function getCreatorFromURL() {
  const params = new URLSearchParams(window.location.search);
  return params.get("name");
}

async function loadCreatorPage() {
  const creator = getCreatorFromURL();

  if (!creator || !VALID_ID.test(creator)) {
    document.getElementById("creator-name").textContent = "Créateur invalide";
    return;
  }

  document.title = "PyNumStore - " + creator;
  document.getElementById("creator-name").textContent = creator; // déjà sûr, textContent ne change pas

  const res = await fetch("data/scripts_index.json");
  const scripts = await res.json();

  const filtered = scripts.filter(s => s.creator === creator);

  const grid = document.getElementById("scripts-grid");
  grid.replaceChildren();

  for (const script of filtered) {
    const metaRes = await fetch(
      `data/${encodeURIComponent(script.creator)}/${encodeURIComponent(script.name)}/metadata.json`
    );
    const meta = await metaRes.json();
    grid.appendChild(buildScriptCard(script, meta));
  }
}