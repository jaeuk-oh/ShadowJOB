from app.config import GOLDEN_SETS_DIR
from app.evaluation.rubric import load_rubric
from app.evaluation.scorer import build_score_schema, score_submission
from app.llm.provider import MockProvider

RUBRIC_PATH = GOLDEN_SETS_DIR / "ax-pm" / "rubric.json"


def _fixed_responder(score_map: dict[str, int]):
    def responder(system: str, user: str):
        out = {cid: {"score": s, "evidence": f"근거-{cid}"} for cid, s in score_map.items()}
        out["overall_comment"] = "총평"
        return out

    return responder


def test_schema_requires_all_criteria():
    r = load_rubric(RUBRIC_PATH)
    schema = build_score_schema(r)
    for cid in r.criterion_ids:
        assert cid in schema["properties"]
        assert cid in schema["required"]
    assert "overall_comment" in schema["required"]


def test_strong_scores_pass():
    r = load_rubric(RUBRIC_PATH)
    provider = MockProvider(_fixed_responder({c.id: 4 for c in r.criteria}))
    ev = score_submission(provider, r, "강한 산출물")
    assert ev.weighted_total == 1.0
    assert ev.passed is True
    assert {s.criterion_id for s in ev.scores} == set(r.criterion_ids)
    assert all(s.evidence for s in ev.scores)  # 근거 필수


def test_weak_scores_fail():
    r = load_rubric(RUBRIC_PATH)
    provider = MockProvider(
        _fixed_responder({"R1": 1, "R2": 1, "R3": 1, "R4": 1, "R5": 2, "R6": 0})
    )
    ev = score_submission(provider, r, "약한 산출물")
    assert ev.passed is False
    assert ev.weighted_total < r.pass_threshold


def test_provider_called_once_per_score():
    r = load_rubric(RUBRIC_PATH)
    provider = MockProvider(_fixed_responder({c.id: 3 for c in r.criteria}))
    score_submission(provider, r, "산출물")
    assert len(provider.calls) == 1
