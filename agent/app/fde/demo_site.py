"""The broken demo site embedded in code, so the sandbox FDE works even on
serverless where the repo's sandbox-site/ folder isn't bundled with the function.

The bug: render() repeats every word, so the hero shows "hi hi my my".
"""

FILES: dict[str, str] = {
    "package.json": '{"name":"lumen-site","version":"0.1.0","private":true}\n',
    "site.js": '''// Lumen Flutes — homepage hero renderer.
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
  console.log(render(HERO).split(" ").slice(0, 4).join(" "));
}

module.exports = { render, HERO };
''',
    "index.html": '''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Lumen Flutes</title>
    <style>
      body { background:#0b0b0b; color:#fff; font-family:Georgia,serif; display:grid; place-items:center; height:100vh; margin:0; }
      h1 { font-size:3rem; }
    </style>
  </head>
  <body>
    <h1 id="hero">…</h1>
    <script src="./site.js"></script>
    <script>
      document.getElementById("hero").textContent =
        (typeof render === "function")
          ? render("hi my name is lumen flutes").split(" ").slice(0, 4).join(" ")
          : "hi my name is";
    </script>
  </body>
</html>
''',
}
