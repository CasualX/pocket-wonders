"use strict";

const form = document.querySelector(".search");
const input = document.getElementById("level-search");
const clear = document.getElementById("clear-search");
const count = document.getElementById("result-count");
const empty = document.getElementById("empty-state");
const levels = [...document.querySelectorAll(".level")];

function filterLevels() {
  const terms = input.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  let visible = 0;
  for (const level of levels) {
    const matches = terms.every(term => level.dataset.search.includes(term));
    level.hidden = !matches;
    if (matches) visible++;
  }
  clear.hidden = !input.value;
  empty.hidden = visible !== 0;
  count.textContent = terms.length ? `${visible} of ${levels.length} levels` : "";
}

form.hidden = false;
form.addEventListener("submit", event => event.preventDefault());
input.addEventListener("input", filterLevels);
input.addEventListener("keydown", event => {
  if (event.key === "Escape") {
    input.value = "";
    filterLevels();
  }
});
clear.addEventListener("click", () => {
  input.value = "";
  filterLevels();
  input.focus();
});
