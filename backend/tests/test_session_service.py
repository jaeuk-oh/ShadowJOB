from app.config import GOLDEN_SETS_DIR
from app.evaluation.rubric import load_rubric
from app.llm.provider import MockProvider
from app.repository.memory import InMemorySessionRepository
from app.services.session_service import SessionService
from app.session.state import State

RUBRIC = load_rubric(GOLDEN_SETS_DIR / "ax-pm" / "rubric.json")
GOLDEN = (GOLDEN_SETS_DIR / "ax-pm" / "golden-01-strong.md").read_text(encoding="utf-8")


def _provider() -> MockProvider:
    def json_responder(system: str, user: str) -> dict:
        if "면접 코치" in system:  # STAR 무기
            return {
                "star_answers": [
                    {
                        "question": "실패 경험은?",
                        "situation": "1차 반려",
                        "task": "근거 보강",
                        "action": "로그 재진단",
                        "result": "통과",
                    }
                ],
                "anticipated_questions": [
                    {"question": "데이터 부족 시?", "suggested_angle": "로그 진단"}
                ],
            }
        # 채점: GOLDEN 마커 있으면 만점, 아니면 최저점
        good = "GOLDEN" in user
        return {
            **{c.id: {"score": 4 if good else 1, "evidence": "e"} for c in RUBRIC.criteria},
            "overall_comment": "ok" if good else "약함",
        }

    def text_responder(system: str, messages: list[dict]) -> str:
        if "편집자" in system:  # 서류 정제
            return "정제된 본문"
        if "매니저" in system or "김도현" in system:  # 반려/대화
            return "도현: 근거가 약해. 다시 가져와."
        return "응답"

    return MockProvider(responder=json_responder, text_responder=text_responder)


def _service():
    return SessionService(
        provider=_provider(),
        repository=InMemorySessionRepository(),
        rubric=RUBRIC,
        golden_text=GOLDEN,
    )


def test_full_cycle_create_chat_submit_reject_revise_pass_weapons():
    svc = _service()

    rec = svc.create_session("saver-studio", max_revisions=1)
    sid = rec.session_id
    assert rec.state == State.TASK_RECEIVED

    # 페르소나 대화 → 히스토리 저장 + 탐색 진입
    reply = svc.chat(sid, "manager-kim-dohyun", "과제 확인했습니다")
    assert reply
    reloaded = svc.get_session(sid)
    assert len(reloaded.persona_histories["manager-kim-dohyun"]) == 2
    assert reloaded.state.value == "exploring"

    # 의사결정 로그
    svc.record_decision(sid, "환불 미해결인데 응답 빠름 → KB 문제 가설")
    assert svc.get_session(sid).decision_logs

    # 1차(약한) 제출 → 반려
    r1 = svc.submit(sid, "WEAK BRIEF: 봇 품질 문제 같음")
    assert r1.evaluation.passed is False
    assert r1.state == "revising"
    assert r1.rejection  # 매니저 피드백 생성됨

    # 2차(골든) 재작업 → 통과 → 완료
    r2 = svc.submit(sid, "GOLDEN BRIEF\n" + GOLDEN)
    assert r2.evaluation.passed is True
    assert r2.state == "completed"

    # 무기 3종
    pkg = svc.get_weapons(sid)
    assert pkg.document_artifact.startswith("📌 가상 실무 프로젝트")
    assert "정제된 본문" in pkg.document_artifact
    assert pkg.star_arsenal["star_answers"]
    assert "과정 기록" in pkg.process_record
    assert "받은 반려 피드백" in pkg.process_record


def test_persona_histories_are_independent():
    svc = _service()
    sid = svc.create_session("saver-studio").session_id
    svc.chat(sid, "manager-kim-dohyun", "매니저에게")
    svc.chat(sid, "engineer-lee-seoyeon", "엔지니어에게")
    rec = svc.get_session(sid)
    mgr = rec.persona_histories["manager-kim-dohyun"]
    eng = rec.persona_histories["engineer-lee-seoyeon"]
    assert all("엔지니어에게" not in t["content"] for t in mgr)
    assert all("매니저에게" not in t["content"] for t in eng)
