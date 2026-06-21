from app.evaluation.scorer import CriterionScore, Evaluation
from app.llm.provider import MockProvider
from app.session.model import SessionRecord
from app.weapons.generator import (
    PROJECT_LABEL,
    generate_package,
    generate_process_record,
)


def _eval(passed, total):
    return Evaluation(
        rubric_id="ax-pm-problem-brief",
        rubric_version="0.1",
        scores=(
            CriterionScore("R2", 4 if passed else 1, "근거 인용 유무"),
            CriterionScore("R3", 4 if passed else 1, "원인 분석 깊이"),
        ),
        weighted_total=total,
        passed=passed,
        overall_comment="c",
    )


def _completed_session() -> SessionRecord:
    s = SessionRecord(session_id="s1", scenario_id="saver-studio", max_revisions=1)
    s.receive_task(); s.start_exploring(); s.start_drafting()
    s.record_decision("엔지니어는 데이터부족이라 했지만 환불 응답이 빨라 인프라가 아닌 KB 문제로 판단")
    s.submit("1차 초안: 봇 품질 문제로 추정")
    s.apply_review(_eval(False, 0.45), rejection_message="근거가 약해. 데이터로 다시 가져와.")
    s.submit("2차: W4 정책변경 인과 + 로그 근거로 KB 갱신 우선")
    s.apply_review(_eval(True, 0.83))
    return s


def test_process_record_is_pure_assembly_with_label():
    s = _completed_session()
    rec = generate_process_record(s)
    assert PROJECT_LABEL in rec
    assert "의사결정 로그" in rec
    assert "엔지니어는 데이터부족" in rec
    assert "받은 반려 피드백" in rec
    assert "1차 제출" in rec and "2차(재작업) 제출" in rec
    assert "개선폭" in rec  # before→after


def test_generate_package_three_weapons():
    s = _completed_session()

    def text_responder(system, messages):
        return "다듬어진 산출물 본문"

    def json_responder(system, user):
        return {
            "star_answers": [
                {
                    "question": "실패 경험은?",
                    "situation": "첫 Brief가 반려됨",
                    "task": "근거 보강",
                    "action": "로그·대시보드로 재진단",
                    "result": "통과",
                }
            ],
            "anticipated_questions": [
                {"question": "데이터 부족 시 판단은?", "suggested_angle": "로그 진단 장면"}
            ],
        }

    provider = MockProvider(responder=json_responder, text_responder=text_responder)
    pkg = generate_package(provider, s)

    # (a) 증거형: 라벨 + 본문
    assert pkg.document_artifact.startswith(PROJECT_LABEL)
    assert "다듬어진 산출물 본문" in pkg.document_artifact
    # (b) 서사형: STAR + 예상질문
    assert len(pkg.star_arsenal["star_answers"]) >= 1
    assert pkg.star_arsenal["anticipated_questions"][0]["question"]
    # (c) 신뢰형: 과정 기록
    assert PROJECT_LABEL in pkg.process_record


def test_package_requires_completed_session():
    s = SessionRecord(session_id="x", scenario_id="saver-studio")
    provider = MockProvider(text_responder=lambda sy, m: "x")
    try:
        generate_package(provider, s)
    except ValueError:
        return
    raise AssertionError("미완료 세션인데 무기 생성됨")
