const deck = JSON.parse(document.getElementById("deck").textContent);
const $ = (id) => document.getElementById(id);
let queue = [], known = 0, shownAt = 0, flipped = false;

function shuffle(a) {
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function start() {
  queue = shuffle([...deck.cards]);
  known = 0;
  $("done").hidden = true;
  $("study").hidden = false;
  show();
}

function show() {
  if (!queue.length) {
    $("study").hidden = true;
    $("done").hidden = false;
    $("summary").textContent = `You learned all ${deck.cards.length} cards.`;
    return;
  }
  flipped = false;
  shownAt = performance.now();
  $("word").textContent = queue[0].front;
  $("example").textContent = "";
  $("actions").hidden = true;
  $("hint").hidden = false;
  $("progress").textContent = `${known} of ${deck.cards.length} learned`;
}

function flip() {
  if (flipped || !queue.length) return;
  flipped = true;
  $("word").textContent = queue[0].back;
  $("example").textContent = queue[0].example || "";
  $("actions").hidden = false;
  $("hint").hidden = true;
}

function answer(ok) {
  if (!flipped) return;
  const card = queue.shift();
  fetch("/api/events", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kind: "card_answered", deck: deck.id, card: card.id,
                           known: ok, ms: Math.round(performance.now() - shownAt) }),
  }).catch(() => {});
  if (ok) known++;
  else queue.splice(Math.min(3, queue.length), 0, card); // see it again in a few cards
  show();
}

$("card").onclick = flip;
$("again").onclick = () => answer(false);
$("got").onclick = () => answer(true);
$("restart").onclick = start;
document.addEventListener("keydown", (e) => {
  if (e.key === "ArrowLeft") answer(false);
  if (e.key === "ArrowRight") answer(true);
});
start();
