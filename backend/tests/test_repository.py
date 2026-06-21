from app.evaluation.scorer import CriterionScore, Evaluation
from app.repository.base import SessionNotFound
from app.repository.memory import InMemorySessionRepository
from app.session.model import SessionRecord


def _record() -> SessionRecord:
    s = SessionRecord(session_id="abc", scenario_id="saver-studio", max_revisions=1)
    s.receive_task(); s.start_drafting()
    s.record_decision("응답시간 빠른데 환불 미해결 → 지식베이스 문제")
    s.persona_histories["manager-kim-dohyun"] = [
        {"role": "user", "content": "과제 확인"},
        {"role": "assistant", "content": "데이터로 가져와"},
    ]
    s.submit("1차 초안")
    s.apply_review(
        Evaluation(
            rubric_id="ax-pm-problem-brief",
            rubric_version="0.1",
            scores=(CriterionScore("R1", 1, "근거 없음"),),
            weighted_total=0.4,
            passed=False,
            overall_comment="약함",
        ),
        rejection_message="다시 보강해서 가져와",
    )
    return s


def test_roundtrip_preserves_everything():
    repo = InMemorySessionRepository()
    original = _record()
    repo.save(original)
    loaded = repo.get("abc")

    assert loaded.to_dict() == original.to_dict()
    # 타입 복원 확인
    assert loaded.state == original.state
    assert loaded.submissions[0].text == "1차 초안"
    assert loaded.evaluations[0].scores[0].criterion_id == "R1"
    assert loaded.rejections == ["다시 보강해서 가져와"]
    assert loaded.decision_logs[0].note.startswith("응답시간")
    assert loaded.persona_histories["manager-kim-dohyun"][1]["content"] == "데이터로 가져와"


def test_exists_and_not_found():
    repo = InMemorySessionRepository()
    assert repo.exists("nope") is False
    try:
        repo.get("nope")
    except SessionNotFound:
        pass
    else:
        raise AssertionError("없는 세션인데 예외 없음")
    repo.save(_record())
    assert repo.exists("abc") is True
