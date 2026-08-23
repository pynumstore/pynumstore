import { getDB, queryOne, queryAll } from "./db.js";
import { initI18n, t } from "./i18n.js";

await initI18n();

async function loadStats() {
  const db = await getDB();

  const totalScripts  = queryOne(db, "SELECT COUNT(*) AS n FROM scripts").n;
  const totalCreators = queryOne(db, "SELECT COUNT(*) AS n FROM creators").n;
  const avg     = queryOne(db, "SELECT ROUND(COUNT(*) * 1.0 / (SELECT COUNT(*) FROM creators), 1) AS n FROM scripts").n;
  const pctDesc = queryOne(db, "SELECT ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM scripts)) AS n FROM scripts WHERE description IS NOT NULL AND description != ''").n;

  const counterTargets = [
    { id: "stat-scripts",  value: totalScripts,  decimals: 0, suffix: ""  },
    { id: "stat-creators", value: totalCreators,  decimals: 0, suffix: ""  },
    { id: "stat-avg",      value: avg,            decimals: 1, suffix: ""  },
    { id: "stat-desc",     value: pctDesc,        decimals: 0, suffix: "%" },
  ];

  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      counterObserver.unobserve(entry.target);
      const t = counterTargets.find(t => t.id === entry.target.id);
      if (t) animateCounter(entry.target, t.value, 900, t.decimals, t.suffix);
    });
  }, { threshold: 0.3 });

  counterTargets.forEach(t => {
    const el = document.getElementById(t.id);
    if (el) counterObserver.observe(el);
  });

  const top10 = queryAll(db, `
    SELECT creator, COUNT(*) AS n
    FROM scripts
    GROUP BY creator
    ORDER BY n DESC
    LIMIT 10
  `);

  const maxCount = top10[0].n;
  const chart    = document.getElementById("creators-chart");

  top10.forEach((row) => {
    const pct = (row.n / maxCount * 100).toFixed(2);

    const rowEl = document.createElement("div");
    rowEl.className = "chart-row";

    const label = document.createElement("a");
    label.href      = `creator.html?name=${encodeURIComponent(row.creator)}`;
    label.className = "chart-label";
    label.textContent = row.creator;

    const barContainer = document.createElement("div");
    barContainer.className = "chart-bar-container";

    const bar = document.createElement("div");
    bar.className = "chart-bar";
    bar.style.setProperty("--pct", `${pct}%`);

    barContainer.appendChild(bar);

    const count = document.createElement("span");
    count.className   = "chart-count";
    count.textContent = row.n.toLocaleString();

    rowEl.append(label, barContainer, count);
    chart.appendChild(rowEl);
  });

  const barObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      barObserver.unobserve(entry.target);
      entry.target.querySelectorAll(".chart-bar").forEach((bar, i) => {
        setTimeout(() => bar.classList.add("animated"), i * 70);
      });
    });
  }, { threshold: 0.1 });

  barObserver.observe(chart);
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

loadStats();