// Lumina — homepage hero renderer.
// SYMPTOM: the homepage hero shows "hi hi my my" instead of the real line.

const HERO = "hi my name is lumina";

function render(text) {
  // BUG: each word is accidentally repeated.
  return text
    .split(" ")
    .map((w) => `${w} ${w}`)
    .join(" ");
}

if (require.main === module) {
  console.log(render(HERO).split(" ").slice(0, 4).join(" "));
}

module.exports = { render, HERO };
