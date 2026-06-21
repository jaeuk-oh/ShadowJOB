from app.evaluation.scorer import CriterionScore, Evaluation
from app.metrics import compute_metrics
from app.repository.memory import InMemorySessionRepository
from app.session.model import SessionRecord


def _eval(passed: bool, total: float) -> Evaluation:
    return Evaluation(
        rubric_id="ax-pm-problem-brief",
        rubric_version="0.1",
        scores=(CriterionScore("R1", 4 if passed else 1, "e"),),
        weighted_total=total,
        passed=passed,
        overall_comment="c",
    )


def _completed(passed: bool, *, revised: bool, star: bool | None) -> SessionRecord:
    s = SessionRecord(session_id="x", scenario_id="saver-studio", max_revisions=1)
    s.receive_task(); s.start_exploring(); s.start_drafting()
    s.submit("1차")
    if revised:
        s.apply_review(_eval(False, 0.4), rejection_message="다시")
        s.submit("2차")
        s.apply_review(_eval(passed, 0.82 if passed else 0.5))
    else:
        s.apply_review(_eval(passed, 0.82 if passed else 0.5))
    if star is not None:
        s.record_survey(star)
    return s


def _in_progress() -> SessionRecord:
    s = SessionRecord(session_id="y", scenario_id="saver-studio")
    s.receive_task(); s.start_exploring()
    return s


def test_metrics_rates():
    records = [
        _completed(True, revised=True, star=True),    # 완주·통과·재작업·STAR yes
        _completed(False, revised=True, star=False),  # 완주·미통과·재작업·STAR no
        _completed(True, revised=False, star=None),   # 완주·통과·설문 미응답
        _in_progress(),                               # 미완주 (exploring에서 멈춤)
    ]
    m = compute_metrics(records)
    assert m["total_sessions"] == 4
    assert m["completed"] == 3
    assert m["completion_rate"] == 0.75
    assert m["passed"] == 2
    assert m["pass_rate"] == round(2 / 3, 4)
    assert m["revised_at_least_once"] == 2
    # STAR: 응답 2건 중 1건 yes
    assert m["survey"]["answered"] == 2
    assert m["survey"]["star_self_report_rate"] == 0.5
    # 퍼널: 3 completed, 1 exploring
    assert m["funnel"]["completed"] == 3
    assert m["funnel"]["exploring"] == 1


def test_blind_eval_rate():
    s = _completed(True, revised=False, star=True)
    s.record_blind_eval(True, evaluator="recruiter-A")
    s.record_blind_eval(False, evaluator="recruiter-B")
    m = compute_metrics([s])
    assert m["blind_eval"]["count"] == 2
    assert m["blind_eval"]["looks_real_rate"] == 0.5


def test_empty_metrics_no_zero_division():
    m = compute_metrics([])
    assert m["total_sessions"] == 0
    assert m["completion_rate"] is None
    assert m["pass_rate"] is None


def test_survey_persists_through_repository_roundtrip():
    repo = InMemorySessionRepository()
    s = _completed(True, revised=True, star=True)
    s.session_id = "keep"
    s.record_blind_eval(True, evaluator="r")
    repo.save(s)
    loaded = repo.get("keep")
    assert loaded.survey_star_self_report is True
    assert loaded.blind_evals[0]["evaluator"] == "r"
    assert len(loaded.events) == len(s.events)
    assert loaded.completed_at is not None
