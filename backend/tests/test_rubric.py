from app.config import GOLDEN_SETS_DIR
from app.evaluation.rubric import (
    load_rubric,
    normalized_weighted_score,
    passed,
)

RUBRIC_PATH = GOLDEN_SETS_DIR / "ax-pm" / "rubric.json"


def test_real_rubric_loads_and_weights_sum_to_one():
    r = load_rubric(RUBRIC_PATH)
    assert r.artifact_type == "problem_brief"
    assert abs(sum(c.weight for c in r.criteria) - 1.0) < 1e-6
    assert r.criterion_ids == ("R1", "R2", "R3", "R4", "R5", "R6")


def test_all_max_scores_normalize_to_one():
    r = load_rubric(RUBRIC_PATH)
    scores = {c.id: r.scale_max for c in r.criteria}
    assert normalized_weighted_score(scores, r) == 1.0
    assert passed(scores, r) is True


def test_all_min_scores_normalize_to_zero():
    r = load_rubric(RUBRIC_PATH)
    scores = {c.id: r.scale_min for c in r.criteria}
    assert normalized_weighted_score(scores, r) == 0.0
    assert passed(scores, r) is False


def test_weak_pattern_fails_threshold():
    r = load_rubric(RUBRIC_PATH)
    # 약한 초안 기대 점수: R1..R4=1, R5=2, R6=0
    scores = {"R1": 1, "R2": 1, "R3": 1, "R4": 1, "R5": 2, "R6": 0}
    total = normalized_weighted_score(scores, r)
    assert total < r.pass_threshold
    assert passed(scores, r) is False


def test_missing_criterion_raises():
    r = load_rubric(RUBRIC_PATH)
    try:
        normalized_weighted_score({"R1": 4}, r)
    except ValueError:
        return
    raise AssertionError("누락 항목인데 예외가 발생하지 않음")
