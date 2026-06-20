"""A fake brand website + social feed for "Lumen Flutes" that the agents scrape
over real HTTP. Its output is controllable (switch scenarios) and mutable (the
Fixer can apply a fix), so we can test the full detect → fix → validate loop."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .scenarios import SCENARIOS, default_product


class ScenarioBody(BaseModel):
    scenario: str


class FixBody(BaseModel):
    action: str  # reset_price | restock


def make_site(scenario: str = "happy_flute") -> FastAPI:
    app = FastAPI(title="Lumen Flutes (fake)")
    app.state.scenario = scenario
    app.state.product = dict(SCENARIOS[scenario].get("product", default_product()))
    app.state.fixes: list[str] = []

    @app.get("/feed")
    async def feed() -> dict[str, Any]:
        sc = SCENARIOS[app.state.scenario]
        if sc.get("error"):
            raise HTTPException(status_code=500, detail="feed temporarily unavailable")
        return {"brand": "Lumen Flutes", "mentions": sc["mentions"]}

    @app.get("/product")
    async def product() -> dict[str, Any]:
        return app.state.product

    @app.post("/admin/scenario")
    async def set_scenario(body: ScenarioBody) -> dict[str, Any]:
        if body.scenario not in SCENARIOS:
            raise HTTPException(status_code=400, detail="unknown scenario")
        app.state.scenario = body.scenario
        app.state.product = dict(SCENARIOS[body.scenario].get("product", default_product()))
        app.state.fixes = []
        return {"ok": True, "scenario": body.scenario, "product": app.state.product}

    @app.post("/admin/fix")
    async def apply_fix(body: FixBody) -> dict[str, Any]:
        p = app.state.product
        if body.action == "reset_price":
            p["price_cents"] = p["msrp_cents"]
        elif body.action == "restock":
            p["in_stock"] = True
        else:
            raise HTTPException(status_code=400, detail="unknown fix action")
        app.state.fixes.append(body.action)
        return {"ok": True, "product": p}

    @app.get("/admin/state")
    async def state() -> dict[str, Any]:
        return {"scenario": app.state.scenario, "product": app.state.product,
                "fixes": app.state.fixes}

    return app
