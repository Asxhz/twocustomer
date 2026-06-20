# Agent simulation — test environment

A self-contained, key-free environment that proves the multi-agent loop works on
a controllable target. Brand: **Lumen Flutes**.

## Pieces
- `fake_brand_site.py` — a FastAPI "brand site" the agents scrape over real HTTP
  (httpx ASGI transport). Its output is switchable (`/admin/scenario`) and mutable
  (`/admin/fix`), so we can test detect → fix → validate.
- `scenarios.py` — the states the site can be in: `happy_flute`, `stockout`,
  `price_bug`, `negative`, `empty`, `dupes`, `error`.
- `agents.py` — four agents that communicate over a message `Bus`:
  - **Monitor** scrapes feed + product, scores signal (real `app.monitor` code), publishes `signal`
  - **Analyst** consumes signals → publishes `insight`
  - **Fixer** consumes fixable insights → calls the site's `/admin/fix` → `fix_applied`
  - **Validator** re-scrapes → confirms `resolved` → `validation`
- `run.py` — narrated run you can watch.

## Run it (no keys needed)
```sh
cd agent
uv run python -m sim.run price_bug     # watch detect → fix → validate
uv run python -m sim.run stockout      # different fix path (restock)
```

## Test it
```sh
cd agent
uv run pytest tests/test_sim.py -v     # 9 edge cases
```

## Edge cases covered
happy path · stockout→restock→validate · **price-bug full repair loop** · negative
quality spike · empty feed · duplicate posts (dedup) · site 500 (graceful) ·
**site switches output mid-run** (agents react) · fix durability (nothing left to fix).

## Extend
Add a scenario to `scenarios.py`, a fix action to `fake_brand_site.py` /admin/fix
+ `agents.detect_product_anomaly`, and a test to `tests/test_sim.py`.
