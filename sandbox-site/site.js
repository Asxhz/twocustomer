// Lumen Flutes — homepage hero renderer.
// SYMPTOM: the homepage hero shows "hi hi my my" instead of the real line.

const HERO = "hi my name is lumen flutes";

function render(text) {
  // BUG: each word is accidentally repeated.
  return text
    .split(" ")
    .map((w) => `${w} ${w}`)
    .join(" ");
}

if (require.main === module) {
  // what the homepage prints (first line of the hero)
  console.log(render(HERO).split(" ").slice(0, 4).join(" "));
}

module.exports = { render, HERO };
