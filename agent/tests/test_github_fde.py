"""GitHub FDE — URL parsing, diff, endpoint wiring (offline)."""

from fastapi.testclient import TestClient

from app.fde import github
from app.main import app

client = TestClient(app)


def test_parse_repo():
    assert github.parse_repo("https://github.com/octocat/Spoon-Knife") == ("octocat", "Spoon-Knife")
    assert github.parse_repo("https://github.com/owner/repo.git") == ("owner", "repo")
    assert github.parse_repo("http://github.com/a/b/") == ("a", "b")
    assert github.parse_repo("https://gitlab.com/a/b") is None
    assert github.parse_repo("not a url") is None
    assert github.parse_repo("") is None


def test_unified_diff():
    d = github.unified_diff("a\nb\n", "a\nc\n", "x.txt")
    assert "-b" in d and "+c" in d and "x.txt" in d


def test_collect_source_skips_deps(tmp_path):
    (tmp_path / "index.html").write_text("<h1>hi</h1>")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "dep.js").write_text("x")
    (tmp_path / "data.bin").write_bytes(b"\x00\x01")
    files = github.collect_source(tmp_path)
    assert "index.html" in files
    assert not any("node_modules" in k for k in files)


def test_github_endpoint_bad_url():
    # invalid repo url returns an error, not a crash
    r = client.post("/fde/github", json={"repo_url": "nope", "symptom": "x"})
    assert r.status_code == 200
    assert "error" in r.json()
