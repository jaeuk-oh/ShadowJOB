"""채점기: 루브릭 → Structured Outputs 스키마/프롬프트 생성 → 채점 결과 파싱.

LLM은 `LLMProvider`로만 호출(테스트는 MockProvider). 채점 일관성(NFR/H3)을 위해:
- 스키마로 출력 형태 강제(항목별 정수 점수 + 근거)
- 프롬프트 고정, 낮은 temperature
- 근거(evidence) 필수 → 근거 없는 고득점 억제
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..llm.provider import LLMProvider
from .rubric import Rubric, normalized_weighted_score


@dataclass(frozen=True)
class CriterionScore:
    criterion_id: str
    score: int
    evidence: str


@dataclass(frozen=True)
class Evaluation:
    rubric_id: str
    rubric_version: str
    scores: tuple[CriterionScore, ...]
    weighted_total: float
    passed: bool
    overall_comment: str

    def score_map(self) -> dict[str, int]:
        return {s.criterion_id: s.score for s in self.scores}


def build_score_schema(rubric: Rubric) -> dict[str, Any]:
    """항목별 {score, evidence} + overall_comment를 강제하는 JSON 스키마."""
    criterion_props = {
        c.id: {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "score": {
                    "type": "integer",
                    "minimum": rubric.scale_min,
                    "maximum": rubric.scale_max,
                    "description": f"{c.name} ({c.id}) 점수",
                },
                "evidence": {
                    "type": "string",
                    "description": "이 점수의 근거 — 산출물 내 인용/로그·지표 참조 포함",
                },
            },
            "required": ["score", "evidence"],
        }
        for c in rubric.criteria
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            **criterion_props,
            "overall_comment": {"type": "string"},
        },
        "required": [*rubric.criterion_ids, "overall_comment"],
    }


def build_scoring_prompt(
    rubric: Rubric, submission_text: str, golden_text: str | None = None
) -> tuple[str, str]:
    lines = [
        "당신은 채용 산출물을 평가하는 엄격하고 일관된 채점관이다.",
        "각 항목을 0~4 정수로 채점하고, 반드시 산출물 속 근거(인용·로그/지표 참조)를 evidence에 적어라.",
        "근거가 없으면 높은 점수를 주지 마라. 후하게 주지 말고 앵커 기준을 그대로 적용하라.",
        "",
        f"[루브릭: {rubric.rubric_id} v{rubric.version}] 척도 {rubric.scale_min}~{rubric.scale_max}",
    ]
    for c in rubric.criteria:
        lines.append(f"- {c.id} {c.name}")
        for level in sorted(c.anchors):
            lines.append(f"    {level}점: {c.anchors[level]}")
    system = "\n".join(lines)

    user_parts = ["[평가 대상 산출물]", submission_text.strip()]
    if golden_text:
        user_parts += [
            "",
            "[참고: 모범답안 방향 — 점수 척도를 정박하는 용도. 그대로 베끼지 말고 기준으로만 사용]",
            golden_text.strip(),
        ]
    user_parts += ["", "위 루브릭에 따라 항목별 점수와 근거, 총평을 JSON으로 출력하라."]
    return system, "\n".join(user_parts)


def score_submission(
    provider: LLMProvider,
    rubric: Rubric,
    submission_text: str,
    golden_text: str | None = None,
    *,
    temperature: float | None = None,
) -> Evaluation:
    schema = build_score_schema(rubric)
    system, user = build_scoring_prompt(rubric, submission_text, golden_text)
    raw = provider.complete_json(
        system=system,
        user=user,
        schema=schema,
        schema_name="rubric_score",
        temperature=temperature,
    )
    scores = tuple(
        CriterionScore(
            criterion_id=c.id,
            score=int(raw[c.id]["score"]),
            evidence=str(raw[c.id]["evidence"]),
        )
        for c in rubric.criteria
    )
    score_map = {s.criterion_id: s.score for s in scores}
    total = normalized_weighted_score(score_map, rubric)
    return Evaluation(
        rubric_id=rubric.rubric_id,
        rubric_version=rubric.version,
        scores=scores,
        weighted_total=total,
        passed=total >= rubric.pass_threshold,
        overall_comment=str(raw.get("overall_comment", "")),
    )
