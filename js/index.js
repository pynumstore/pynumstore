import { buildScriptCard } from "./utils.js";

async function loadScripts() {
  const grid = document.getElementById("scripts-grid");
  grid.replaceChildren();

  const res = await fetch("data/scripts_index.json");
  const scripts = await res.json();

  const shuffled = scripts.sort(() => Math.random() - 0.5);
  const selected = shuffled.slice(0, 12);

  await Promise.all(selected.map(async script => {
    const metaRes = await fetch(
      `data/${encodeURIComponent(script.creator)}/${encodeURIComponent(script.name)}/metadata.json`
    );
    const meta = await metaRes.json();
    grid.appendChild(buildScriptCard(script, meta));
  }));
}

document.addEventListener("DOMContentLoaded", loadScripts);