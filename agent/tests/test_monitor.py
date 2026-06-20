"""P3.20/P3.22/P3.25 — normalize, dedup, adaptive scoring (offline)."""

from app.monitor.dedup import dedup
from app.monitor.mention import normalize
from app.monitor.scoring import Baseline, score_batch


def test_normalize_stable_id():
    a = normalize("web", text="hello world", url="https://x.com/p/1")
    b = normalize("web", text="hello world", url="https://x.com/p/1")
    assert a.external_id == b.external_id  # deterministic hash
    assert a.platform == "web"


def test_dedup_filters_seen():
    seen: set[str] = set()
    m1 = normalize("x", text="a", external_id="1")
    m2 = normalize("x", text="b", external_id="2")
    first = dedup([m1, m2], seen)
    assert len(first) == 2
    # re-run with the same ids → nothing fresh
    again = dedup([normalize("x", text="a", external_id="1")], seen)
    assert again == []


def test_scoring_monotonic_and_threshold():
    base = Baseline()
    low = normalize("x", text="meh", external_id="l", engagement=1)
    high = normalize("x", text="viral", external_id="h", engagement=500)
    score_batch([low], base)
    score_batch([high], base)
    assert high.score > low.score
    assert high.high_signal is True
    assert low.high_signal is False
