# Lumina demo site (deliberately broken)

A tiny static site for testing TwoCustomer's forward-deployed fix.

**The bug:** `site.js` `render()` repeats every word, so the hero shows
`hi hi my my` instead of `hi my name is lumina`.

**Test it:** connect this repo in TwoCustomer → `/admin/fix` → "Connected repo" →
symptom "the homepage hero shows hi hi my my" → it diagnoses `site.js`, opens a PR,
and (on a build host) returns a live preview of the fix.

Static — Vercel serves it with zero config.
