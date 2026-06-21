"""매니저 반려 피드백 생성 (FR-5 / FR-11).

평가 엔진의 채점 결과(항목별 점수+근거)를 매니저 페르소나의 목소리로 변환한다.
- 고정 멘트 금지: 실제 약점(낮은 점수 항목과 그 근거)에 반응하는 피드백.
- 정답을 떠먹이지 않음: 무엇이 약한지 짚되 어떻게 고칠지는 사용자가 생각하게.
"""
from __future__ import annotations

from ..evaluation.rubric import Rubric
from ..evaluation.scorer import Evaluation
from ..llm.provider import LLMProvider
from .loader import Persona


def _weak_criteria(evaluation: Evaluation, rubric: Rubric) -> list[tuple[str, int, str]]:
    """절반 이하 점수 항목을 (이름, 점수, 근거)로. 없으면 가장 낮은 항목."""
    mid = (rubric.scale_min + rubric.scale_max) / 2
    weak = []
    for s in evaluation.scores:
        if s.score <= mid:
            weak.append((rubric.criterion(s.criterion_id).name, s.score, s.evidence))
    if not weak:
        lowest = min(evaluation.scores, key=lambda s: s.score)
        weak = [(rubric.criterion(lowest.criterion_id).name, lowest.score, lowest.evidence)]
    return weak


def build_manager_feedback(
    provider: LLMProvider,
    manager_persona: Persona,
    evaluation: Evaluation,
    rubric: Rubric,
    *,
    temperature: float | None = None,
) -> str:
    weak = _weak_criteria(evaluation, rubric)
    weak_lines = "\n".join(f"- {name} (점수 {score}/{rubric.scale_max}): {ev}" for name, score, ev in weak)

    instruction = f"""[내부 평가 결과 — 너(매니저)만 본다]
방금 부하직원의 1차 Problem Brief를 평가했다. 통과 임계 {rubric.pass_threshold} 기준 결과:
- 총점(0~1): {evaluation.weighted_total}
- 통과 여부: {"통과" if evaluation.passed else "반려"}
약점 항목:
{weak_lines}

위 약점을 근거로, 김도현답게 슬랙 메시지 한 통으로 **구체적으로 짚으며 반려**하라.
규칙:
- 위 약점 1~2개를 콕 집어 말한다(어느 부분이 왜 약한지). 일반론·고정 멘트 금지.
- 정답을 알려주지 말 것. "다시 보강해서 가져와" 식으로 재작업을 요구.
- 짧고 현실적으로(3~6문장). 인신공격 금지.
""".strip()

    return provider.complete_text(
        system=manager_persona.system_prompt,
        messages=[{"role": "user", "content": instruction}],
        temperature=temperature,
    )
