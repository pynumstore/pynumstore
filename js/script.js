function getQueryParams() {
  const params = new URLSearchParams(window.location.search);
  return {
    creator: params.get("creator"),
    name: params.get("name")
  };
}

async function loadScriptPage() {
  const { creator, name } = getQueryParams();

  const res = await fetch(`data/${creator}/${name}/metadata.json`);
  const script = await res.json();

  document.title = `PyNumStore - ${script.name}`;

  document.querySelector(".name").textContent = script.name;
  document.querySelector(".creator").innerHTML =
    `By <a href="creator.html?name=${creator}">${creator}</a>`;

  document.querySelector(".created-at").textContent =
    `Created on ${script.created_at}`;

  document.querySelector(".size").textContent =
    `Size: ${script.size}`;

  document.getElementById("numworks-link").href =
    `https://my.numworks.com/python/${script.creator}/${script.name}/`;

  document.getElementById("script-image").src =
    `${script.image}`;

  if (script.description) {
    document.querySelector(".description").innerHTML =
      `<h2>Description:</h2><div class="divider"></div><p>${script.description}</p>`;
  }

  const tagsContainer = document.querySelector(".tags");
  if (script.tags && script.tags.length) {
    tagsContainer.innerHTML =
      "<h2>Tags:</h2><div class=\"divider\"></div>" +
      script.tags.map(t => `<p>#${t}</p>`).join("");
  }
}