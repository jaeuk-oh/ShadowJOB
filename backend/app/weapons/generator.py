"""무기 3종 생성기 (FR-7 — 핵심 차별점).

완료된 SessionRecord에서 funnel 3단계 무기를 추출:
- (a) 증거형: 서류 산출물 정제본 ("가상 실무 프로젝트" 라벨 / 정직한 포지셔닝, PRD §5·NFR)
- (b) 서사형: 면접 STAR + 예상질문 탄약고 (반려→재작업 성장 서사 활용)
- (c) 신뢰형: 과정 기록 (의사결정 로그 + 반려 후 수정 이력) — 대부분 순수 조립

(a)(b)는 LLMProvider, (c)는 데이터 조립. 테스트는 MockProvider로.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..llm.provider import LLMProvider
from ..session.model import SessionRecord

# 정직한 포지셔닝 (PRD §5 원칙4 / NFR: 포지셔닝 정직성)
PROJECT_LABEL = "📌 가상 실무 프로젝트 — FIELD 시뮬레이션 기반 (실제 고용 경력 아님)"


@dataclass(frozen=True)
class WeaponPackage:
    document_artifact: str          # (a) 증거형
    star_arsenal: dict[str, Any]    # (b) 서사형
    process_record: str             # (c) 신뢰형


# ---------- (a) 증거형: 서류 산출물 정제본 ----------

def generate_document(provider: LLMProvider, session: SessionRecord) -> str:
    final = session.final_submission
    if final is None:
        raise ValueError("제출물이 없어 서류 산출물을 만들 수 없습니다.")
    system = (
        "너는 신입 지원자의 실무 산출물을 '제출 가능한 형태'로 다듬는 편집자다. "
        "내용·주장·근거를 바꾸거나 새로 지어내지 마라. 구조·표현·가독성만 개선한다."
    )
    user = (
        "다음 산출물을 다듬어라. 사실/근거는 그대로 유지하고 표현만 명료하게.\n\n"
        f"{final.text.strip()}"
    )
    refined = provider.complete_text(system=system, messages=[{"role": "user", "content": user}])
    return f"{PROJECT_LABEL}\n\n{refined.strip()}"


# ---------- (b) 서사형: STAR + 예상질문 ----------

_STAR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "star_answers": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "question": {"type": "string"},
                    "situation": {"type": "string"},
                    "task": {"type": "string"},
                    "action": {"type": "string"},
                    "result": {"type": "string"},
                },
                "required": ["question", "situation", "task", "action", "result"],
            },
        },
        "anticipated_questions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "question": {"type": "string"},
                    "suggested_angle": {"type": "string"},
                },
                "required": ["question", "suggested_angle"],
            },
        },
    },
    "required": ["star_answers", "anticipated_questions"],
}


def _growth_context(session: SessionRecord) -> str:
    parts: list[str] = []
    if session.first_submission:
        parts.append(f"[1차 제출 요약]\n{session.first_submission.text.strip()[:1200]}")
    if session.rejections:
        parts.append(f"[받은 반려 피드백]\n{session.rejections[-1].strip()}")
    if session.final_submission and len(session.submissions) > 1:
        parts.append(f"[최종 제출 요약]\n{session.final_submission.text.strip()[:1200]}")
    if session.decision_logs:
        logs = "\n".join(f"- {d.note}" for d in session.decision_logs)
        parts.append(f"[의사결정 로그]\n{logs}")
    return "\n\n".join(parts)


def generate_star(provider: LLMProvider, session: SessionRecord) -> dict[str, Any]:
    system = (
        "너는 취업 면접 코치다. 아래 '가상 실무 프로젝트' 경험을 면접에서 말할 수 있는 "
        "STAR(상황·과제·행동·결과) 답변과 예상질문 탄약고로 변환한다. "
        "경력인 척하지 말고 '프로젝트 경험'으로 정직하게. 반려를 극복한 성장 서사를 적극 활용하라."
    )
    user = (
        "다음 경험 자료로 STAR 답변 2~3개(특히 '실패/피드백 극복' 포함)와 "
        "예상 면접질문 3~5개를 만들어라.\n\n" + _growth_context(session)
    )
    return provider.complete_json(
        system=system, user=user, schema=_STAR_SCHEMA, schema_name="star_arsenal"
    )


# ---------- (c) 신뢰형: 과정 기록 (순수 조립) ----------

def generate_process_record(session: SessionRecord) -> str:
    lines = [PROJECT_LABEL, "", "# 과정 기록 (의사결정 + 반려 후 수정 이력)", ""]

    lines.append("## 의사결정 로그")
    if session.decision_logs:
        for d in session.decision_logs:
            lines.append(f"- ({d.created_at}) {d.note}")
    else:
        lines.append("- (기록 없음)")
    lines.append("")

    lines.append("## 제출·심사 이력")
    for i, sub in enumerate(session.submissions):
        label = "1차" if i == 0 else f"{i+1}차(재작업)"
        ev = session.evaluations[i] if i < len(session.evaluations) else None
        score = f"총점 {ev.weighted_total} ({'PASS' if ev.passed else 'FAIL'})" if ev else "미채점"
        lines.append(f"### {label} 제출 — {score}")
        if ev:
            for s in ev.scores:
                lines.append(f"  - {s.criterion_id} {s.score}점: {s.evidence}")
    lines.append("")

    if session.rejections:
        lines.append("## 받은 반려 피드백")
        for r in session.rejections:
            lines.append(f"> {r.strip()}")
        lines.append("")

    if len(session.submissions) >= 2 and len(session.evaluations) >= 2:
        before = session.evaluations[0].weighted_total
        after = session.evaluations[-1].weighted_total
        lines.append("## 개선폭 (before → after)")
        lines.append(f"- 총점 {before} → {after}")

    return "\n".join(lines)


# ---------- 패키지 ----------

def generate_package(provider: LLMProvider, session: SessionRecord) -> WeaponPackage:
    if not session.is_completed:
        raise ValueError("완료된 세션에서만 무기를 생성할 수 있습니다.")
    return WeaponPackage(
        document_artifact=generate_document(provider, session),
        star_arsenal=generate_star(provider, session),
        process_record=generate_process_record(session),
    )
