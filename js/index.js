async function loadScripts() {
  const grid = document.getElementById("scripts-grid");

  const res = await fetch("data/scripts_index.json");
  const scripts = await res.json();

  const shuffled = scripts.sort(() => Math.random() - 0.5);

  const selected = shuffled.slice(0, 12);

  for (const script of selected) {
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
          <img src="${meta.image}" alt="Script Image">
        </div>
      </div>
    `;

    grid.appendChild(card);
  }
}
