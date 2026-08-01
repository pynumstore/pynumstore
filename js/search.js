import { getDB, queryAll } from "./db.js";
import { buildScriptCard } from "./utils.js";

let db;

const SORT_OPTIONS = [
  { value: "name-asc",   label: "A → Z"     },
  { value: "name-desc",  label: "Z → A"     },
  { value: "date-desc",  label: "Newest update"    },
  { value: "date-asc",   label: "Oldest update"    },
  { value: "size-desc",  label: "Largest"   },
  { value: "size-asc",   label: "Smallest"  },
];

const SIZE_CATEGORIES = [
  { value: "tiny",   label: "< 1 KB",     sql: "size < 1024"                  },
  { value: "small",  label: "1 – 10 KB",  sql: "size BETWEEN 1024 AND 10239"  },
  { value: "medium", label: "10 – 50 KB", sql: "size BETWEEN 10240 AND 51199" },
  { value: "large",  label: "> 50 KB",    sql: "size >= 51200"                },
];

async function initSearch() {
  document.getElementById("scripts").style.display = "none";
  db = await getDB();
  buildSortPills();
  buildSizeCheckboxes();
  attachListeners();
  restoreFromURL();
  runSearch();
}

function buildSortPills() {
  const bar = document.getElementById("sort-buttons");
  SORT_OPTIONS.forEach(({ value, label }) => {
    const btn = document.createElement("button");
    btn.className    = "sort-btn";
    btn.dataset.sort = value;
    btn.textContent  = label;
    btn.addEventListener("click", () => {
      document.querySelectorAll("#sort-buttons .sort-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      runSearch(true);
    });
    bar.appendChild(btn);
  });
}

function buildSizeCheckboxes() {
  const container = document.getElementById("size-filters");
  SIZE_CATEGORIES.forEach(({ value, label }) => {
    const pill     = document.createElement("label");
    pill.className = "size-pill";
    const cb       = document.createElement("input");
    cb.type        = "checkbox";
    cb.value       = value;
    cb.addEventListener("change", () => runSearch(true));
    pill.append(cb, document.createTextNode(label));
    container.appendChild(pill);
  });
}

function attachListeners() {
  document.getElementById("advanced-toggle").addEventListener("click", () => {
    const panel  = document.getElementById("advanced-panel");
    const isOpen = panel.classList.toggle("open");
    document.getElementById("advanced-toggle").textContent =
      isOpen ? "▴ Advanced filters" : "▾ Advanced filters";
  });
  document.getElementById("date-from").addEventListener("change", () => runSearch(true));
  document.getElementById("date-to").addEventListener("change", () => runSearch(true));
  document.getElementById("search-button").addEventListener("click", () => runSearch(true));
  document.getElementById("search-input").addEventListener("keypress", e => {
    if (e.key === "Enter") runSearch(true);
  });
}

function restoreFromURL() {
  const p = new URLSearchParams(window.location.search);
  if (p.get("q"))         document.getElementById("search-input").value = p.get("q");
  if (p.get("field"))     document.getElementById("field-select").value = p.get("field");
  if (p.get("date_from")) document.getElementById("date-from").value    = p.get("date_from");
  if (p.get("date_to"))   document.getElementById("date-to").value      = p.get("date_to");

  const sort = p.get("sort") ?? "name-asc";
  document.querySelectorAll("#sort-buttons .sort-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.sort === sort);
  });

  const sizes = p.get("sizes") ? p.get("sizes").split(",") : [];
  document.querySelectorAll("#size-filters input[type=checkbox]").forEach(cb => {
    cb.checked = sizes.includes(cb.value);
  });

  if (p.get("date_from") || p.get("date_to") || p.get("sizes")) {
    document.getElementById("advanced-panel").classList.add("open");
    document.getElementById("advanced-toggle").textContent = "▴ Advanced filters";
  }
}

function parseQuery(raw) {
  const result = { creator: [], tags: [], name: [], description: [], text: [] };

  const re = /([@#%$])?"([^"]+)"|([@#%$])(\S+)|(\S+)/g;
  let m;

  while ((m = re.exec(raw)) !== null) {
    if (m[2] !== undefined) {
      pushToken(result, m[1] ?? "", m[2], true);
    } else if (m[4] !== undefined) {
      if (m[4]) pushToken(result, m[3], m[4], false);
    } else if (m[5] !== undefined) {
      const w = m[5];
      if ("@#%$".includes(w[0]) && w.length > 1) pushToken(result, w[0], w.slice(1), false);
      else pushToken(result, "", w, false);
    }
  }

  return result;
}

function pushToken(result, prefix, value, strict) {
  const token = { value, strict };
  if      (prefix === "@") result.creator.push(token);
  else if (prefix === "#") result.tags.push(token);
  else if (prefix === "%") result.name.push(token);
  else if (prefix === "$") result.description.push(token);
  else                     result.text.push(token);
}

function addCondition(conditions, values, strict, fuzzySQL, fuzzyVal, strictSQL, strictVal) {
  if (strict) { conditions.push(strictSQL); values.push(strictVal); }
  else        { conditions.push(fuzzySQL);  values.push(fuzzyVal);  }
}

function buildQuery({ q, field, sort, date_from, date_to, sizes, page }) {
  const parsed     = parseQuery(q);
  const conditions = [];
  const values     = [];

  parsed.creator.forEach(({ value, strict }) =>
    addCondition(conditions, values, strict,
      "creator LIKE ?", `%${value}%`,
      "creator = ?",    value)
  );

  parsed.tags.forEach(({ value, strict }) =>
    addCondition(conditions, values, strict,
      "tags LIKE ?",                                   `%${value}%`,
      "(',' || COALESCE(tags,'') || ',') LIKE ?",     `%,${value},%`)
  );

  parsed.name.forEach(({ value, strict }) =>
    addCondition(conditions, values, strict,
      "name LIKE ?", `%${value}%`,
      "name = ?",    value)
  );

  parsed.description.forEach(({ value, strict }) =>
    addCondition(conditions, values, strict,
      "description_text LIKE ?",                              `%${value}%`,
      "(' ' || COALESCE(description_text,'') || ' ') LIKE ?", `% ${value} %`)
  );

  parsed.text.forEach(({ value, strict }) => {
    if (field === "creator") {
      addCondition(conditions, values, strict,
        "creator LIKE ?", `%${value}%`, "creator = ?", value);
    } else if (field === "name") {
      addCondition(conditions, values, strict,
        "name LIKE ?", `%${value}%`, "name = ?", value);
    } else if (field === "description") {
      addCondition(conditions, values, strict,
        "description_text LIKE ?",                              `%${value}%`,
        "(' ' || COALESCE(description_text,'') || ' ') LIKE ?", `% ${value} %`);
    } else if (field === "tags") {
      addCondition(conditions, values, strict,
        "tags LIKE ?",                                      `%${value}%`,
        "(',' || COALESCE(tags,'') || ',') LIKE ?",         `%,${value},%`);
    } else {
      if (strict) {
        conditions.push("(name = ? OR creator = ? OR (' ' || COALESCE(description_text,'') || ' ') LIKE ?)");
        values.push(value, value, `% ${value} %`);
      } else {
        conditions.push("(name LIKE ? OR creator LIKE ? OR description_text LIKE ?)");
        values.push(`%${value}%`, `%${value}%`, `%${value}%`);
      }
    }
  });

  if (date_from) { conditions.push("updated_at >= ?"); values.push(date_from); }
  if (date_to)   { conditions.push("updated_at <= ?"); values.push(date_to);   }

  if (sizes.length > 0 && sizes.length < 4) {
    const sizeConds = SIZE_CATEGORIES.filter(c => sizes.includes(c.value)).map(c => c.sql);
    if (sizeConds.length) conditions.push(`(${sizeConds.join(" OR ")})`);
  }

  const where    = conditions.length ? "WHERE " + conditions.join(" AND ") : "";
  const hasQuery = conditions.length > 0;

  const sortMap = {
    "name-asc":  "name ASC",
    "name-desc": "name DESC",
    "date-desc": "updated_at DESC",
    "date-asc":  "updated_at ASC",
    "size-desc": "size DESC",
    "size-asc":  "size ASC",
    };  
  
  const orderBy = sortMap[sort] ?? "name ASC";

  const offset = (page - 1) * 30;

  return {
    sql: `
      SELECT name, creator, thumbnail 
      FROM scripts 
      ${where}
      ORDER BY ${orderBy}
      LIMIT 30 OFFSET ?
    `,
    countSql: `
      SELECT COUNT(*) 
      FROM scripts 
      ${where}
    `,
    values: [...values, offset],
    countValues: values,
    hasQuery,
  };
}

function getParams() {
  return {
    q:         document.getElementById("search-input").value.trim(),
    field:     document.getElementById("field-select").value,
    sort:      document.querySelector("#sort-buttons .sort-btn.active")?.dataset.sort ?? "name-asc",
    date_from: document.getElementById("date-from").value,
    date_to:   document.getElementById("date-to").value,
    sizes:     [...document.querySelectorAll("#size-filters input:checked")].map(cb => cb.value),
    page:      Math.max(1, Number(new URLSearchParams(window.location.search).get("page")) || 1),
  };
}

function runSearch(resetPage = false) {
  const params = getParams();

  if (resetPage) {
    params.page = 1;
  }

  const { sql, countSql, values, countValues, hasQuery } = buildQuery(params);

  if (!params.q) {
    document.getElementById("scripts").style.display = "none";
    document.getElementById("advanced").style.display = "block";
    return;
  }

  const url = new URL(window.location.href);

  params.q
    ? url.searchParams.set("q", params.q)
    : url.searchParams.delete("q");

  params.field !== "all"
    ? url.searchParams.set("field", params.field)
    : url.searchParams.delete("field");

  params.sort !== "name-asc"
    ? url.searchParams.set("sort", params.sort)
    : url.searchParams.delete("sort");

  params.date_from
    ? url.searchParams.set("date_from", params.date_from)
    : url.searchParams.delete("date_from");

  params.date_to
    ? url.searchParams.set("date_to", params.date_to)
    : url.searchParams.delete("date_to");

  params.sizes.length
    ? url.searchParams.set("sizes", params.sizes.join(","))
    : url.searchParams.delete("sizes");

  params.page > 1
    ? url.searchParams.set("page", params.page)
    : url.searchParams.delete("page");

  history.replaceState(null, "", url);

  const scripts = queryAll(db, sql, values);
  const total = queryAll(db, countSql, countValues)[0]["COUNT(*)"];

  document.getElementById("advanced").style.display = "none";
  document.getElementById("scripts").style.display = "block";

  render(scripts, params.q, hasQuery, total);
  renderPagination(total, params.page);
}

function render(scripts, query, hasQuery, total) {
  const grid = document.getElementById("results");
  grid.replaceChildren();

  for (const script of scripts) {
    grid.appendChild(buildScriptCard(script));
  }

  const title = document.getElementById("results-title");

  title.textContent = hasQuery
    ? `${total} result${total !== 1 ? "s" : ""}`
    : `${scripts.length} random scripts`;

  document.title = query
    ? `PyNumStore - Search for "${query}"`
    : "PyNumStore - Search";
}

function renderPagination(total, currentPage) {

  const container = document.getElementById("pagination");
  container.replaceChildren();

  const totalPages = Math.ceil(total / 30);

  if (totalPages <= 1) return;

  function addPage(page) {
    const link = document.createElement("a");

    const url = new URL(window.location.href);
    url.searchParams.set("page", page);

    link.href = url.toString();
    link.textContent = page;

    if (page === currentPage) {
      link.classList.add("active");
    }

    container.appendChild(link);
  }

  function addDots() {
    const span = document.createElement("span");
    span.textContent = "...";
    span.className = "pagination-dots";
    container.appendChild(span);
  }

  addPage(1);

  let start = Math.max(2, currentPage - 2);
  let end   = Math.min(totalPages - 1, currentPage + 2);

  if (start > 2) {
    addDots();
  }

  for (let i = start; i <= end; i++) {
    addPage(i);
  }

  if (end < totalPages - 1) {
    addDots();
  }

  if (totalPages > 1) {
    addPage(totalPages);
  }
}

document.addEventListener("DOMContentLoaded", initSearch);