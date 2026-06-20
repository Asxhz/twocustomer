"""P1.22 / P1.24 — registry listing + dispatch (incl. unknown + error paths)."""

import pytest

from app.tools import echo  # noqa: F401 - registers echo
from app.tools.registry import Tool, ToolRegistry, registry


def test_registry_lists_echo():
    assert "echo" in registry.names()
    specs = registry.specs()
    assert any(s["name"] == "echo" and "input_schema" in s for s in specs)


@pytest.mark.asyncio
async def test_dispatch_echo():
    out = await registry.dispatch("echo", {"message": "hi"})
    assert out == "echo: hi"


@pytest.mark.asyncio
async def test_dispatch_unknown_tool_returns_error():
    out = await registry.dispatch("nope", {})
    assert out.startswith("ERROR")


@pytest.mark.asyncio
async def test_dispatch_tool_exception_is_caught():
    r = ToolRegistry()

    async def boom() -> str:
        raise ValueError("kaboom")

    r.register(Tool(name="boom", description="x", input_schema={"type": "object"},
                    run=boom))
    out = await r.dispatch("boom", {})
    assert "ERROR running boom" in out and "kaboom" in out


def test_double_register_rejected():
    r = ToolRegistry()

    async def fn() -> str:
        return "ok"

    t = Tool(name="dup", description="x", input_schema={"type": "object"}, run=fn)
    r.register(t)
    with pytest.raises(ValueError):
        r.register(t)
