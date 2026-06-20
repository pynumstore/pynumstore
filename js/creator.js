function getCreatorFromURL() {
  const params = new URLSearchParams(window.location.search);
  return params.get("name");
}

async function loadCreatorPage() {

  const creator = getCreatorFromURL();

  document.title = "PyNum Store - " + creator;

  document.getElementById("creator-name").textContent = creator;

  const res = await fetch("data/scripts_index.json");
  const scripts = await res.json();

  const filtered = scripts.filter(s => s.creator === creator);

  const grid = document.getElementById("scripts-grid");

  for (const script of filtered) {
    const metaRes = await fetch(
      `data/${script.creator}/${script.name}/metadata.json`
    );
    const meta = await metaRes.json();

    const card = document.createElement("a");
    card.href = `script.html?creator=${script.creator}&name=${script.name}`;

    card.innerHTML = `
      <div class="card">
        <p class="card-tag">${script.creator}</p>
        <h3>${script.name}</h3>
        <div class="img-wrapper">
          <img src="${meta.image}">
        </div>
      </div>
    `;

    grid.appendChild(card);
  }
}