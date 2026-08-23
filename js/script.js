import { getDB, queryOne } from "./db.js";
import { initI18n, t, getCurrentLang } from "./i18n.js";
import { DEFAULT_THUMBNAIL } from "./utils.js";

await initI18n();

const VALID_CREATOR = /^[a-z0-9]([a-z0-9-]{0,48}[a-z0-9])?$/;
const VALID_NAME    = /^[a-z_][a-z0-9_]{0,49}$/;

let currentScript  = null;
let currentCreator = null;

async function loadScriptPage() {
  const params  = new URLSearchParams(window.location.search);
  const creator = params.get("creator");
  const name    = params.get("name");

  if (!creator || !name || !VALID_CREATOR.test(creator) || !VALID_NAME.test(name)) {
    showNotFound();
    return;
  }

  const db     = await getDB();
  const script = queryOne(db, `
    SELECT * FROM scripts
    WHERE creator = ? AND name = ?
  `, [creator, name]);

  if (!script) {
    showNotFound();
    return;
  }

  currentScript  = script;
  currentCreator = creator;

  renderScript();

  document.getElementById("numworks-link").href =
    `https://my.numworks.com/python/${encodeURIComponent(creator)}/${encodeURIComponent(name)}/`;

  const scriptImage = document.getElementById("script-image");
  scriptImage.onerror = () => {
    scriptImage.onerror = null;
    scriptImage.src = DEFAULT_THUMBNAIL;
  };
  scriptImage.src = script.thumbnail;

  document.addEventListener("i18n:changed", renderScript);
}

function showNotFound() {
  document.title = t("script.titleDefault");
  document.querySelector(".name").textContent = t("script.notFound");
}

function renderScript() {
  const script = currentScript;
  document.title = t("script.titleName", { name: script.name });
  document.querySelector(".name").textContent = script.name;

  const creatorEl = document.querySelector(".creator");
  creatorEl.replaceChildren(`${t("script.by")} `);
  const creatorLink = document.createElement("a");
  creatorLink.href        = `creator.html?name=${encodeURIComponent(currentCreator)}`;
  creatorLink.textContent = currentCreator;
  creatorEl.appendChild(creatorLink);

  const locale = getCurrentLang() === "fr" ? "fr-FR" : "en-US";
  const date   = new Date(script.updated_at + "T00:00:00");
  document.querySelector(".updated-at").textContent = t("script.lastUpdated", {
    date: date.toLocaleDateString(locale, { year: "numeric", month: "long", day: "numeric" })
  });
  document.querySelector(".size").textContent = formatSize(script.size, locale);

  if (script.description) {
    const descSection = document.querySelector(".description");
    descSection.replaceChildren();

    const h2 = document.createElement("h2");
    h2.textContent = t("script.description");

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
    tags = script.tags ? script.tags.split(",").map(tag => tag.trim()).filter(Boolean) : [];
  } catch {
    tags = [];
  }

  const tagsContainer = document.querySelector(".tags");
  if (tags.length) {
    tagsContainer.replaceChildren();

    const h2 = document.createElement("h2");
    h2.textContent = t("script.tags");

    const divider = document.createElement("div");
    divider.className = "divider";

    tagsContainer.append(h2, divider);

    for (const tag of tags) {
      const p = document.createElement("p");
      p.textContent = `#${tag}`;
      tagsContainer.appendChild(p);
    }
  }
}

function formatSize(bytes, locale) {
    if (!bytes) return t("script.unknownSize");
    if (bytes < 1024) return t("script.bytes", { size: bytes });
    const kb = (bytes / 1024).toLocaleString(locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return `${kb} ${t("script.kb")}`;
}

loadScriptPage();