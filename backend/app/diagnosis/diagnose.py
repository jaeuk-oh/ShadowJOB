"""진단·개인화 앞단 퍼널 (P1.5).

기존 이력서/포폴 텍스트를 직무 역량 체크리스트(진단 루브릭)로 채점 → 개선점·부족한점(갭)을
뽑고, 시뮬에서 강조할 역량(recommended_focus)을 제안한다.

설계: 평가 엔진을 **그대로 재사용**한다(`score_submission`은 artifact-agnostic).
진단은 시뮬을 대체하지 않고, "필요한 것 중심"으로 시뮬을 시작하게 하는 개인화 레이어다.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..evaluation.rubric import Rubric
from ..evaluation.scorer import CriterionScore, Evaluation, score_submission
from ..llm.provider import LLMProvider

# 진단 약점 항목 → 시뮬에서 강조할 포커스 안내 (개인화 메시지)
FOCUS_MAP: dict[str, str] = {
    "D1": "직무 적합성이 약합니다 — 이번 시뮬에서 AX PM 핵심 판단(문제 정의·AI 이해)을 직접 보여주세요.",
    "D2": "성과를 숫자로 못 보여줬어요 — 시뮬에서 '지표로 말하기'(성공 측정 지표)를 의식적으로 연습하세요.",
    "D3": "문제해결 서사가 약합니다 — 시뮬의 반려→재작업 과정을 '문제→판단→결과'로 남기세요.",
    "D4": "명료성이 약합니다 — Brief를 30초에 읽히는 구조로 쓰는 데 집중하세요.",
    "D5": "직무 키워드/스킬 노출이 약합니다 — 데이터·AI·협업 맥락을 실제 행동으로 드러내세요.",
}


@dataclass(frozen=True)
class FocusItem:
    criterion_id: str
    area: str
    message: str


@dataclass(frozen=True)
class DiagnosisReport:
    rubric_id: str
    rubric_version: str
    weighted_total: float
    meets_bar: bool
    scores: tuple[CriterionScore, ...]
    gaps: tuple[CriterionScore, ...]            # 임계 이하 항목(개선점·부족한점)
    recommended_focus: tuple[FocusItem, ...]    # 시뮬에서 강조할 것
    summary: str

    def gap_ids(self) -> list[str]:
        return [g.criterion_id for g in self.gaps]


def diagnose(
    provider: LLMProvider, rubric: Rubric, resume_text: str
) -> DiagnosisReport:
    if not resume_text.strip():
        raise ValueError("진단할 이력서/포폴 텍스트가 비어 있습니다.")

    ev: Evaluation = score_submission(provider, rubric, resume_text)  # 골든 없이 절대 평가
    mid = (rubric.scale_min + rubric.scale_max) / 2
    gaps = tuple(s for s in ev.scores if s.score <= mid)

    focus = tuple(
        FocusItem(
            criterion_id=g.criterion_id,
            area=rubric.criterion(g.criterion_id).name,
            message=FOCUS_MAP.get(g.criterion_id, "이 영역을 시뮬에서 보완하세요."),
        )
        for g in gaps
    )

    return DiagnosisReport(
        rubric_id=ev.rubric_id,
        rubric_version=ev.rubric_version,
        weighted_total=ev.weighted_total,
        meets_bar=ev.passed,
        scores=ev.scores,
        gaps=gaps,
        recommended_focus=focus,
        summary=ev.overall_comment,
    )
