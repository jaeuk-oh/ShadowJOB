"""베타 계측 집계 (P1-23 / PRD §3 성공 기준).

세션 레코드들에서 북극성 검증용 지표를 계산한다:
- 완주율(completion) · 통과율(pass) · STAR 자가응답률 · 블라인드 '진짜 같다' 비율
- 단계별 퍼널(어디서 이탈하는지)
순수 로직 — 저장소에서 받은 list[SessionRecord]만 입력.
"""
from __future__ import annotations

from typing import Any

from ..session.model import SessionRecord
from ..session.state import State

# 퍼널 순서 (도달 최대 단계 집계용)
_FUNNEL = [
    State.ONBOARDING,
    State.TASK_RECEIVED,
    State.EXPLORING,
    State.DRAFTING,
    State.UNDER_REVIEW,
    State.REVISING,
    State.COMPLETED,
]
_ORDER = {s.value: i for i, s in enumerate(_FUNNEL)}


def _rate(numer: int, denom: int) -> float | None:
    return round(numer / denom, 4) if denom else None


def _furthest_state(rec: SessionRecord) -> str:
    """events에 기록된 도달 단계 중 가장 멀리 간 것(없으면 현재 state)."""
    best = rec.state.value
    for ev in rec.events:
        if ev["type"].startswith("state:"):
            s = ev["type"].split(":", 1)[1]
            if _ORDER.get(s, -1) > _ORDER.get(best, -1):
                best = s
    return best


def compute_metrics(records: list[SessionRecord]) -> dict[str, Any]:
    total = len(records)
    completed = [r for r in records if r.is_completed]
    n_completed = len(completed)

    # 완주율: 시작(세션 생성)한 전체 중 완료 비율
    completion_rate = _rate(n_completed, total)

    # 통과율: 완료된 것 중 최종 통과
    n_passed = sum(1 for r in completed if r.passed)
    pass_rate = _rate(n_passed, n_completed)

    # 1차 반려 후 재작업 발생률(반려 루프가 실제로 도는지)
    n_revised = sum(1 for r in records if r.revisions_used >= 1)

    # STAR 자가응답
    survey_answered = [r for r in records if r.survey_star_self_report is not None]
    survey_yes = sum(1 for r in survey_answered if r.survey_star_self_report)
    star_self_report_rate = _rate(survey_yes, len(survey_answered))

    # 블라인드 평가('진짜 실무자 결과물 같다')
    blind = [b for r in records for b in r.blind_evals]
    blind_yes = sum(1 for b in blind if b.get("looks_real"))
    blind_looks_real_rate = _rate(blind_yes, len(blind))

    # 퍼널 (도달 최대 단계별 세션 수)
    funnel: dict[str, int] = {s.value: 0 for s in _FUNNEL}
    for r in records:
        funnel[_furthest_state(r)] += 1

    return {
        "total_sessions": total,
        "completed": n_completed,
        "completion_rate": completion_rate,        # 목표 ≥ 0.50
        "passed": n_passed,
        "pass_rate": pass_rate,
        "revised_at_least_once": n_revised,
        "survey": {
            "answered": len(survey_answered),
            "star_self_report_yes": survey_yes,
            "star_self_report_rate": star_self_report_rate,  # 목표 ≥ 0.70
        },
        "blind_eval": {
            "count": len(blind),
            "looks_real_yes": blind_yes,
            "looks_real_rate": blind_looks_real_rate,        # 목표 ≥ 0.60
        },
        "funnel": funnel,
        "targets": {  # PRD §3 가설 합격선(측정 후 확정)
            "completion_rate": 0.50,
            "star_self_report_rate": 0.70,
            "blind_looks_real_rate": 0.60,
        },
    }
