// Change to the full API Gateway URL when testing locally outside of CloudFront
const API_URL = "/api/solve";

const TOP_N = 10;

const CYCLE = ["X", "G", "Y"];
const TILE_CLASS = { X: "grey", G: "green", Y: "yellow" };

let tileStates = ["X", "X", "X", "X", "X"];
let guesses = [];

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("#tiles .tile").forEach((tile, i) =>
    tile.addEventListener("click", () => cycleTile(i))
  );

  document.getElementById("word-input").addEventListener("input", syncLetters);
  document.getElementById("word-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") submitGuess();
  });
  document.getElementById("submit-btn").addEventListener("click", submitGuess);
  document.getElementById("reset-btn").addEventListener("click", reset);

  document.getElementById("word-input").focus();
  loadOpeners();
});

// ── Tile interactions ─────────────────────────────────────────────────────────

function cycleTile(index) {
  tileStates[index] = CYCLE[(CYCLE.indexOf(tileStates[index]) + 1) % 3];
  renderTiles();
}

function syncLetters() {
  const letters = document.getElementById("word-input").value
    .toUpperCase()
    .replace(/[^A-Z]/g, "")
    .slice(0, 5);
  document.querySelectorAll("#tiles .tile").forEach((tile, i) => {
    tile.textContent = letters[i] ?? "?";
  });
}

function renderTiles() {
  document.querySelectorAll("#tiles .tile").forEach((tile, i) => {
    tile.className = "tile " + TILE_CLASS[tileStates[i]];
  });
}

// ── Submit ────────────────────────────────────────────────────────────────────

async function fetchSuggestions(guessList) {
  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ guesses: guessList }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function loadOpeners() {
  try {
    renderResults(await fetchSuggestions([]));
  } catch {
    // Stay quiet — suggestions will appear after the first guess instead.
  }
}

async function submitGuess() {
  clearError();

  const raw = document.getElementById("word-input").value.toUpperCase().replace(/[^A-Z]/g, "");
  if (raw.length !== 5) {
    showError("Enter a 5-letter word first.");
    return;
  }

  const result = tileStates.join("");

  if (result === "GGGGG") {
    guesses.push({ word: raw, result });
    appendHistory(raw, result);
    resetInput();
    showSolved(raw);
    return;
  }

  setLoading(true);
  try {
    const data = await fetchSuggestions([...guesses, { word: raw, result }]);
    guesses.push({ word: raw, result });
    appendHistory(raw, result);
    resetInput();
    renderResults(data);
  } catch {
    showError("Could not reach the solver — please try again.");
  } finally {
    setLoading(false);
  }
}

// ── History ───────────────────────────────────────────────────────────────────

function appendHistory(word, result) {
  const row = document.createElement("div");
  row.className = "history-row";
  for (let i = 0; i < 5; i++) {
    const tile = document.createElement("div");
    tile.className = "tile small " + TILE_CLASS[result[i]];
    tile.textContent = word[i];
    row.appendChild(tile);
  }
  document.getElementById("history").appendChild(row);
}

// ── Results ───────────────────────────────────────────────────────────────────

function renderResults(data) {
  const section = document.getElementById("results");
  section.hidden = false;

  const count = data.candidates_count;
  const countEl = document.getElementById("candidates-count");

  if (count === 0) {
    countEl.textContent = "No matching words found — check your inputs.";
    document.getElementById("freq-list").innerHTML = "";
    document.getElementById("info-list").innerHTML = "";
    return;
  }

  if (count === 1) {
    countEl.textContent = `The answer must be: ${data.frequency_ranked[0]?.word}`;
  } else if (guesses.length === 0) {
    countEl.textContent = `Best opening guesses (${count.toLocaleString()} words in play)`;
  } else {
    countEl.textContent = `${count.toLocaleString()} possible word${count !== 1 ? "s" : ""} remaining`;
  }

  renderList("freq-list", data.frequency_ranked.slice(0, TOP_N), ({ word, score }) =>
    `<span class="result-word">${word}</span><span class="result-score">${score}</span>`
  );

  // Before any guess every word is trivially a candidate — skip the markers.
  const markCandidates = guesses.length > 0;
  renderList("info-list", data.info_ranked.slice(0, TOP_N), ({ word, score, is_candidate }) => {
    const star = markCandidates && is_candidate ? '<span class="star">*</span>' : "";
    return `<span class="result-word">${word}${star}</span><span class="result-score">${score}/100</span>`;
  }, (item) => markCandidates && item.is_candidate ? "candidate" : "");
}

function renderList(id, items, toHTML, className = () => "") {
  const list = document.getElementById(id);
  list.innerHTML = "";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.innerHTML = toHTML(item);
    const cls = className(item);
    if (cls) li.classList.add(cls);
    list.appendChild(li);
  });
}

function showSolved(word) {
  const section = document.getElementById("results");
  section.hidden = false;
  document.getElementById("candidates-count").textContent = `Solved! The word was ${word}.`;
  document.getElementById("freq-list").innerHTML = "";
  document.getElementById("info-list").innerHTML = "";
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function resetInput() {
  tileStates = ["X", "X", "X", "X", "X"];
  document.getElementById("word-input").value = "";
  syncLetters();
  renderTiles();
}

function reset() {
  guesses = [];
  document.getElementById("history").innerHTML = "";
  document.getElementById("results").hidden = true;
  resetInput();
  clearError();
  document.getElementById("word-input").focus();
  loadOpeners();
}

function setLoading(on) {
  const btn = document.getElementById("submit-btn");
  btn.disabled = on;
  btn.textContent = on ? "Calculating…" : "Get Suggestions";
}

function showError(msg) {
  let el = document.getElementById("error-msg");
  if (!el) {
    el = document.createElement("p");
    el.id = "error-msg";
    document.getElementById("input-section").appendChild(el);
  }
  el.textContent = msg;
}

function clearError() {
  document.getElementById("error-msg")?.remove();
}
