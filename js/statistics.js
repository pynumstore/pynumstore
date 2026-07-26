import { getDB, queryOne } from "./db.js";

async function loadStats() {
  const db = await getDB();

  const totalScripts  = queryOne(db, "SELECT COUNT(*) AS n FROM scripts").n;
  const totalCreators = queryOne(db, "SELECT COUNT(*) AS n FROM creators").n;
  const avg           = queryOne(db, "SELECT ROUND(COUNT(*) * 1.0 / (SELECT COUNT(*) FROM creators), 1) AS n FROM scripts").n;
  const pctDesc       = queryOne(db, "SELECT ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM scripts)) AS n FROM scripts WHERE description IS NOT NULL AND description != ''").n;
  const top           = queryOne(db, "SELECT creator, COUNT(*) AS n FROM scripts GROUP BY creator ORDER BY n DESC LIMIT 1");

  document.getElementById("stat-top-name").textContent  = top.creator;
  document.getElementById("stat-top-count").textContent = top.n.toLocaleString();
  document.getElementById("stat-top-link").href =
    `creator.html?name=${encodeURIComponent(top.creator)}`;

  const targets = [
    { id: "stat-scripts",  value: totalScripts,  decimals: 0, suffix: ""  },
    { id: "stat-creators", value: totalCreators,  decimals: 0, suffix: ""  },
    { id: "stat-avg",      value: avg,            decimals: 1, suffix: ""  },
    { id: "stat-desc",     value: pctDesc,        decimals: 0, suffix: "%" },
  ];

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      observer.unobserve(entry.target);
      const t = targets.find(t => t.id === entry.target.id);
      if (t) animateCounter(entry.target, t.value, 900, t.decimals, t.suffix);
    });
  }, { threshold: 0.3 });

  targets.forEach(t => {
    const el = document.getElementById(t.id);
    if (el) observer.observe(el);
  });
}

function animateCounter(el, target, duration, decimals, suffix) {
  const start = performance.now();

  function update(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased    = 1 - Math.pow(1 - progress, 3);
    const current  = eased * target;

    el.textContent = (decimals > 0
      ? current.toFixed(decimals)
      : Math.floor(current).toLocaleString()) + suffix;

    if (progress < 1) {
      requestAnimationFrame(update);
    } else {
      el.textContent = (decimals > 0
        ? target.toFixed(decimals)
        : target.toLocaleString()) + suffix;
    }
  }

  requestAnimationFrame(update);
}

document.addEventListener("DOMContentLoaded", loadStats);