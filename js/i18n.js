const COOKIE_NAME = "pns_lang";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 365;
const SUPPORTED_LANGS = ["en", "fr"];
const DEFAULT_LANG = "en";

let currentLang = DEFAULT_LANG;
let dict = {};

setTimeout(() => document.documentElement.classList.remove("i18n-pending"), 2000);

function getCookie(name) {
  const match = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[1]) : null;
}

function setCookie(name, value) {
  document.cookie = `${name}=${encodeURIComponent(value)}; max-age=${COOKIE_MAX_AGE}; path=/; SameSite=Lax`;
}

function detectLang() {
  const cookieLang = getCookie(COOKIE_NAME);
  if (cookieLang && SUPPORTED_LANGS.includes(cookieLang)) return cookieLang;

  const browserLangs = navigator.languages || [navigator.language || ""];
  for (const l of browserLangs) {
    if (l.toLowerCase().startsWith("fr")) return "fr";
  }
  return DEFAULT_LANG;
}

async function loadDict(lang) {
  const res = await fetch(`data/i18n/${lang}.json`);
  if (!res.ok) throw new Error(`Impossible to load data/i18n/${lang}.json`);
  return res.json();
}

function get(key) {
  return key.split(".").reduce((o, k) => (o && o[k] !== undefined ? o[k] : undefined), dict);
}

export function t(key, vars = {}) {
  const val = get(key);
  if (val === undefined) return key;
  return typeof val === "string"
    ? val.replace(/{([^}]+)}/g, (match, p1) => (vars[p1] !== undefined ? vars[p1] : match))
    : val;
}

function applyTranslations() {
  document.documentElement.lang = currentLang;

  document.querySelectorAll("[data-i18n]").forEach(el => {
    el.textContent = t(el.getAttribute("data-i18n"), el.textContent);
  });

  document.querySelectorAll("[data-i18n-html]").forEach(el => {
    el.innerHTML = t(el.getAttribute("data-i18n-html"), el.innerHTML);
  });

  ["placeholder", "title", "aria-label", "alt"].forEach(attr => {
    document.querySelectorAll(`[data-i18n-${attr}]`).forEach(el => {
      el.setAttribute(attr, t(el.getAttribute(`data-i18n-${attr}`), el.getAttribute(attr)));
    });
  });

  document.querySelectorAll("[data-lang-switch]").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-lang-switch") === currentLang);
  });

  document.documentElement.classList.remove("i18n-pending");
}

export async function setLang(lang) {
  if (!SUPPORTED_LANGS.includes(lang) || lang === currentLang) return;
  currentLang = lang;
  setCookie(COOKIE_NAME, lang);
  dict = await loadDict(lang);
  applyTranslations();
  document.dispatchEvent(new CustomEvent("i18n:changed", { detail: { lang, t } }));
}

export async function initI18n() {
  currentLang = detectLang();
  setCookie(COOKIE_NAME, currentLang);
  dict = await loadDict(currentLang);
  applyTranslations();

  document.querySelectorAll("[data-lang-switch]").forEach(btn => {
    btn.addEventListener("click", () => setLang(btn.getAttribute("data-lang-switch")));
  });

  document.dispatchEvent(new CustomEvent("i18n:changed", { detail: { lang: currentLang, t } }));
  return currentLang;
}

export function getCurrentLang() {
  return currentLang;
}