const VALID_ID = /^[a-z0-9-]{1,50}$/;

function getQueryParams() {
  const params = new URLSearchParams(window.location.search);
  return {
    creator: params.get("creator"),
    name: params.get("name")
  };
}

async function loadScriptPage() {
  const { creator, name } = getQueryParams();

  if (!creator || !name || !VALID_ID.test(creator) || !VALID_ID.test(name)) {
    document.querySelector(".name").textContent = "Script introuvable.";
    return;
  }

  const res = await fetch(`data/${encodeURIComponent(creator)}/${encodeURIComponent(name)}/metadata.json`);
  if (!res.ok) {
    document.querySelector(".name").textContent = "Script introuvable.";
    return;
  }
  const script = await res.json();

  document.title = `PyNumStore - ${script.name}`;
  document.querySelector(".name").textContent = script.name;

  const creatorEl = document.querySelector(".creator");
  creatorEl.textContent = "By ";
  const creatorLink = document.createElement("a");
  creatorLink.href = `creator.html?name=${encodeURIComponent(creator)}`;
  creatorLink.textContent = creator;
  creatorEl.appendChild(creatorLink);

  document.querySelector(".created-at").textContent = `Created on ${script.created_at}`;
  document.querySelector(".size").textContent = `Size: ${script.size}`;

  document.getElementById("numworks-link").href =
    `https://my.numworks.com/python/${encodeURIComponent(script.creator)}/${encodeURIComponent(script.name)}/`;

  document.getElementById("script-image").src = script.image;

  if (script.description) {
    const descSection = document.querySelector(".description");
    descSection.replaceChildren();
    const h2 = document.createElement("h2");
    h2.textContent = "Description:";
    const divider = document.createElement("div");
    divider.className = "divider";
    const p = document.createElement("p");
    p.textContent = script.description;
    descSection.append(h2, divider, p);
  }

  const tagsContainer = document.querySelector(".tags");
  if (script.tags && script.tags.length) {
    tagsContainer.replaceChildren();
    const h2 = document.createElement("h2");
    h2.textContent = "Tags:";
    const divider = document.createElement("div");
    divider.className = "divider";
    tagsContainer.append(h2, divider);
    for (const t of script.tags) {
      const p = document.createElement("p");
      p.textContent = `#${t}`;
      tagsContainer.appendChild(p);
    }
  }
}