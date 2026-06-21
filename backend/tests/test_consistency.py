import itertools

from app.config import GOLDEN_SETS_DIR
from app.evaluation.consistency import measure_consistency
from app.evaluation.rubric import load_rubric
from app.llm.provider import MockProvider

RUBRIC_PATH = GOLDEN_SETS_DIR / "ax-pm" / "rubric.json"


def _const_responder(score_map):
    def responder(system, user):
        out = {cid: {"score": s, "evidence": "e"} for cid, s in score_map.items()}
        out["overall_comment"] = "c"
        return out

    return responder


def _sequence_responder(score_maps):
    """run마다 다른 점수를 돌려주는 불안정 채점관 시뮬레이션."""
    cycle = itertools.cycle(score_maps)

    def responder(system, user):
        sm = next(cycle)
        out = {cid: {"score": s, "evidence": "e"} for cid, s in sm.items()}
        out["overall_comment"] = "c"
        return out

    return responder


def test_deterministic_scoring_is_stable():
    r = load_rubric(RUBRIC_PATH)
    provider = MockProvider(_const_responder({c.id: 3 for c in r.criteria}))
    report = measure_consistency(provider, r, "산출물", runs=5)
    assert report.total_stdev == 0.0
    assert report.total_spread == 0.0
    assert report.pass_flips is False
    assert report.unstable is False
    assert len(provider.calls) == 5  # runs회 호출


def test_fluctuating_scoring_flagged_unstable():
    r = load_rubric(RUBRIC_PATH)
    high = {c.id: 4 for c in r.criteria}
    low = {c.id: 0 for c in r.criteria}
    provider = MockProvider(_sequence_responder([high, low]))
    report = measure_consistency(provider, r, "산출물", runs=4)
    assert report.total_stdev > 0.05
    assert report.pass_flips is True
    assert report.unstable is True
