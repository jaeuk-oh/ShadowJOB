from app.config import GOLDEN_SETS_DIR
from app.diagnosis.diagnose import diagnose
from app.evaluation.rubric import load_rubric
from app.llm.provider import MockProvider

RUBRIC = load_rubric(GOLDEN_SETS_DIR / "ax-pm" / "diagnosis-rubric.json")


def _provider(score: int):
    def json_responder(system, user):
        out = {c.id: {"score": score, "evidence": f"e-{c.id}"} for c in RUBRIC.criteria}
        out["overall_comment"] = "총평"
        return out

    return MockProvider(responder=json_responder)


def test_diagnosis_rubric_valid():
    assert RUBRIC.artifact_type == "resume_portfolio"
    assert RUBRIC.criterion_ids == ("D1", "D2", "D3", "D4", "D5")
    assert abs(sum(c.weight for c in RUBRIC.criteria) - 1.0) < 1e-6


def test_weak_resume_many_gaps_with_focus():
    rep = diagnose(_provider(1), RUBRIC, "경력 나열만 있는 약한 이력서")
    # 전 항목 1점(≤ 중간값 2) → 전부 갭
    assert len(rep.gaps) == len(RUBRIC.criteria)
    assert rep.meets_bar is False
    # 갭마다 시뮬 강조 포커스가 도출됨(개인화)
    assert {f.criterion_id for f in rep.recommended_focus} == set(rep.gap_ids())
    assert all(f.message for f in rep.recommended_focus)


def test_strong_resume_few_gaps():
    rep = diagnose(_provider(4), RUBRIC, "성과가 지표로 드러난 강한 이력서")
    assert rep.gaps == ()
    assert rep.recommended_focus == ()
    assert rep.meets_bar is True
    assert rep.weighted_total == 1.0


def test_empty_resume_raises():
    try:
        diagnose(_provider(3), RUBRIC, "   ")
    except ValueError:
        return
    raise AssertionError("빈 이력서인데 예외 없음")
