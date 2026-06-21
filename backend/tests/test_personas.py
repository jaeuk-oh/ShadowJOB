from app.config import GOLDEN_SETS_DIR
from app.evaluation.rubric import load_rubric
from app.evaluation.scorer import CriterionScore, Evaluation
from app.llm.provider import MockProvider
from app.personas.feedback import build_manager_feedback
from app.personas.loader import (
    ACTING_GUARD,
    list_persona_ids,
    load_all_personas,
    load_persona,
)
from app.personas.orchestrator import SessionPersonas

SCENARIO = "saver-studio"
RUBRIC_PATH = GOLDEN_SETS_DIR / "ax-pm" / "rubric.json"


def _echo_text_provider():
    # 시스템 프롬프트의 인물 + 마지막 사용자 메시지를 반영한 가짜 응답
    def text_responder(system: str, messages: list[dict[str, str]]) -> str:
        last = messages[-1]["content"] if messages else ""
        tag = "MANAGER" if "매니저" in system else ("CUSTOMER" if "고객" in system else "OTHER")
        return f"[{tag}] 받았어요: {last[:20]}"

    return MockProvider(text_responder=text_responder)


def test_three_personas_loaded():
    ids = list_persona_ids(SCENARIO)
    assert set(ids) == {
        "manager-kim-dohyun",
        "customer-park-sangwoo",
        "engineer-lee-seoyeon",
    }


def test_persona_system_prompt_has_card_and_guard():
    p = load_persona(SCENARIO, "manager-kim-dohyun")
    assert p.name.startswith("김도현")
    assert "연기 규칙" in p.system_prompt
    assert ACTING_GUARD in p.system_prompt
    assert "AI" in p.system_prompt  # AI 비노출 가드 포함


def test_orchestrator_routes_and_keeps_independent_history():
    provider = _echo_text_provider()
    session = SessionPersonas.create(SCENARIO, provider)
    assert len(session.persona_ids()) == 3

    r1 = session.send("manager-kim-dohyun", "과제 확인했습니다")
    assert r1.startswith("[MANAGER]")
    session.send("customer-park-sangwoo", "안녕하세요")

    # 히스토리 독립성: 매니저 대화에 고객 메시지가 섞이지 않음
    mgr_hist = session.transcript("manager-kim-dohyun")
    assert len(mgr_hist) == 2  # user + assistant
    assert all("안녕하세요" not in t["content"] for t in mgr_hist)


def test_unknown_persona_raises():
    provider = _echo_text_provider()
    session = SessionPersonas.create(SCENARIO, provider)
    try:
        session.send("nobody", "hi")
    except KeyError:
        return
    raise AssertionError("없는 페르소나인데 예외 없음")


def test_manager_feedback_reacts_to_weak_criteria():
    rubric = load_rubric(RUBRIC_PATH)
    # 낮은 점수 평가 결과(반려 대상)
    evaluation = Evaluation(
        rubric_id=rubric.rubric_id,
        rubric_version=rubric.version,
        scores=tuple(
            CriterionScore(c.id, 1 if c.id in {"R2", "R3"} else 3, f"근거-{c.id}")
            for c in rubric.criteria
        ),
        weighted_total=0.5,
        passed=False,
        overall_comment="근거 부족",
    )

    captured = {}

    def text_responder(system: str, messages: list[dict[str, str]]) -> str:
        captured["prompt"] = messages[-1]["content"]
        return "도현: 근거가 약해. 다시 보강해서 가져와."

    provider = MockProvider(text_responder=text_responder)
    manager = load_persona(SCENARIO, "manager-kim-dohyun")
    msg = build_manager_feedback(provider, manager, evaluation, rubric)

    # 피드백 프롬프트가 실제 약점 항목명을 담아 '반응'하는지(고정 멘트 아님)
    assert "데이터 근거의 충실성" in captured["prompt"]
    assert "원인 분석의 깊이" in captured["prompt"]
    assert "반려" in captured["prompt"]
    assert msg
