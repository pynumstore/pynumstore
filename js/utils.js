export const DEFAULT_THUMBNAIL =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 320 241' role='img' aria-label='Thumbnail unavailable'%3E%3Crect width='320' height='241' fill='%23F0ECE3'/%3E%3Crect x='0.5' y='0.5' width='319' height='240' fill='none' stroke='%231f1f1f' stroke-opacity='0.12'/%3E%3Cg transform='translate(110,78)' fill='none' stroke='%23A79E8E' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='0' y='0' width='100' height='76' rx='6'/%3E%3Ccircle cx='23' cy='23' r='8' fill='none'/%3E%3Cpath d='M0 60 L28 36 L52 55 L74 32 L100 52'/%3E%3C/g%3E%3C/svg%3E";

export function buildScriptCard(script) {
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
  img.onerror = () => {
    img.onerror = null;
    img.src = DEFAULT_THUMBNAIL;
  };
  img.src = script.thumbnail;
  img.alt = script.name;
  imgWrapper.appendChild(img);

  cardDiv.append(tag, h3, imgWrapper);
  card.appendChild(cardDiv);
  return card;
}