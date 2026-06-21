from app.evaluation.scorer import CriterionScore, Evaluation
from app.session.model import SessionRecord
from app.session.state import (
    InvalidTransition,
    State,
    can_transition,
    next_after_review,
)


def _eval(passed: bool, total: float) -> Evaluation:
    return Evaluation(
        rubric_id="ax-pm-problem-brief",
        rubric_version="0.1",
        scores=(CriterionScore("R1", 4 if passed else 1, "e"),),
        weighted_total=total,
        passed=passed,
        overall_comment="c",
    )


def test_state_machine_allowed_and_blocked():
    assert can_transition(State.DRAFTING, State.UNDER_REVIEW)
    assert not can_transition(State.ONBOARDING, State.COMPLETED)
    assert not can_transition(State.COMPLETED, State.DRAFTING)


def test_next_after_review_logic():
    assert next_after_review(passed=True, revisions_used=0, max_revisions=1) == State.COMPLETED
    assert next_after_review(passed=False, revisions_used=0, max_revisions=1) == State.REVISING
    assert next_after_review(passed=False, revisions_used=1, max_revisions=1) == State.COMPLETED


def test_full_cycle_reject_then_pass():
    s = SessionRecord(session_id="s1", scenario_id="saver-studio", max_revisions=1)
    s.receive_task()
    s.start_exploring()
    s.start_drafting()
    s.record_decision("응답시간 빠른데 환불 미해결 → 지식베이스 문제로 판단")

    s.submit("1차 초안")
    assert s.state == State.UNDER_REVIEW
    dst = s.apply_review(_eval(passed=False, total=0.5), rejection_message="근거가 약해. 다시.")
    assert dst == State.REVISING
    assert s.rejections == ["근거가 약해. 다시."]

    s.submit("2차 재작업")  # REVISING -> UNDER_REVIEW
    assert s.revisions_used == 1
    dst2 = s.apply_review(_eval(passed=True, total=0.82))
    assert dst2 == State.COMPLETED
    assert s.is_completed and s.passed
    assert s.first_submission.text == "1차 초안"
    assert s.final_submission.text == "2차 재작업"


def test_completes_even_if_revisions_exhausted_without_pass():
    s = SessionRecord(session_id="s2", scenario_id="saver-studio", max_revisions=1)
    s.receive_task(); s.start_drafting()
    s.submit("1차")
    s.apply_review(_eval(False, 0.4), rejection_message="보강 필요")
    s.submit("2차")
    dst = s.apply_review(_eval(False, 0.6))  # 여전히 미통과지만 반려 소진
    assert dst == State.COMPLETED
    assert s.is_completed and not s.passed


def test_submit_in_wrong_state_raises():
    s = SessionRecord(session_id="s3", scenario_id="saver-studio")
    try:
        s.submit("바로 제출 불가")
    except InvalidTransition:
        return
    raise AssertionError("온보딩 상태 제출인데 예외 없음")
