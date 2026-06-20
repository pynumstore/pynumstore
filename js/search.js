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
  grid.textContent = "";

  for (const script of list) {

    const key = `${script.creator}/${script.name}`;

    if (!metadataCache[key]) {
      const res = await fetch(`data/${key}/metadata.json`);
      metadataCache[key] = await res.json();
    }

    const meta = metadataCache[key];

    const card = document.createElement("a");
    card.href = `script.html?creator=${script.creator}&name=${script.name}`;

    card.innerHTML = `
      <div class="card">
        <div class="img-wrapper">
          <img src="${meta.image}" alt="">
        </div>

        <p class="card-tag">${script.creator}</p>
        <h3>${script.name}</h3>
      </div>
    `;

    grid.appendChild(card);
  }

  document.title = query
      ? `PyNum Store - Search for "${query}"`
      : `PyNum Store - Search`;
    
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