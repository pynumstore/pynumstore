export function buildScriptCard(script, meta) {
  const card = document.createElement("a");
  card.href = `script.html?creator=${encodeURIComponent(script.creator)}&name=${encodeURIComponent(script.name)}`;

  const cardDiv = document.createElement("div");
  cardDiv.className = "card";

  const tag = document.createElement("p");
  tag.className = "card-tag";
  tag.textContent = script.creator;

  const h3 = document.createElement("h3");
  h3.textContent = script.name;

  const imgWrapper = document.createElement("div");
  imgWrapper.className = "img-wrapper";
  const img = document.createElement("img");
  img.src = meta.image;
  img.alt = script.name;
  imgWrapper.appendChild(img);

  cardDiv.append(tag, h3, imgWrapper);
  card.appendChild(cardDiv);
  return card;
}