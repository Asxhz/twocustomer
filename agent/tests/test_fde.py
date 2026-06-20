"""V3 FDE sandbox — isolation, validate (runs node), patch, protections."""

import os

import pytest

from app.fde import sandbox
from app.tools.registry import registry


def test_tool_registered():
    import app.tools.fix_site_tool  # noqa: F401
    assert "fix_site" in registry.names()


def test_prepare_sandbox_isolated():
    sb = sandbox.prepare_sandbox()
    assert sb.exists() and sb.name == "sandbox-site"
    # it's a COPY in a temp dir, not the repo's sandbox-site
    assert str(sb) != str(sandbox.TARGET_SITE)
    assert (sb / "site.js").exists()


@pytest.mark.asyncio
async def test_broken_site_validates_as_unhealthy():
    sb = sandbox.prepare_sandbox()
    out, healthy = await sandbox.validate(sb)
    assert out == "hi hi my my"
    assert healthy is False


@pytest.mark.asyncio
async def test_apply_known_patch_then_validate_healthy():
    """Mechanics (no Claude): apply a correct patch -> validate -> healthy."""
    sb = sandbox.prepare_sandbox()
    fixed = (sb / "site.js").read_text().replace(
        "`${w} ${w}`", "`${w}`")  # remove the word-doubling bug
    sandbox.apply_patch(sb, "site.js", fixed)
    out, healthy = await sandbox.validate(sb)
    assert out == "hi my name is"
    assert healthy is True


def test_protections_reject_traversal_and_blocked():
    sb = sandbox.prepare_sandbox()
    with pytest.raises(ValueError):
        sandbox.apply_patch(sb, "../escape.js", "x")     # path traversal
    with pytest.raises(ValueError):
        sandbox.apply_patch(sb, ".env", "SECRET=1")      # blocked file
    with pytest.raises(ValueError):
        sandbox.apply_patch(sb, "evil.sh", "rm -rf /")   # not allow-listed ext


@pytest.mark.live
@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="no Anthropic key")
@pytest.mark.asyncio
async def test_claude_fixes_site_live():
    res = await sandbox.fix_site("the homepage hero renders 'hi hi my my'")
    assert res["resolved"] is True
    assert res["after"] == "hi my name is"
    assert res["file"].endswith("site.js")
