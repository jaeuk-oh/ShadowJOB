"""채점 일관성 하니스 (가설 H3 / NFR: 채점 일관성).

동일 산출물을 N회 반복 채점해 편차를 측정한다.
- 항목별 점수 표준편차, 총점(0..1) 표준편차/최대-최소 스프레드, 통과여부 흔들림(flip).
- 임계 초과 시 unstable=True → 회귀 테스트에서 실패시킬 수 있는 신호.
실서비스에서는 OpenAIProvider로, 테스트에서는 MockProvider로 동일하게 돌린다.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass

from ..llm.provider import LLMProvider
from .rubric import Rubric
from .scorer import Evaluation, score_submission


@dataclass(frozen=True)
class ConsistencyReport:
    runs: int
    per_criterion_stdev: dict[str, float]
    total_mean: float
    total_stdev: float
    total_spread: float  # max - min
    pass_flips: bool  # 통과/불통과가 run마다 갈렸는가
    unstable: bool
    evaluations: tuple[Evaluation, ...]


def measure_consistency(
    provider: LLMProvider,
    rubric: Rubric,
    submission_text: str,
    golden_text: str | None = None,
    *,
    runs: int = 5,
    max_total_stdev: float = 0.05,
    max_criterion_stdev: float = 1.0,
) -> ConsistencyReport:
    if runs < 2:
        raise ValueError("일관성 측정은 runs>=2 필요")

    evals = tuple(
        score_submission(provider, rubric, submission_text, golden_text)
        for _ in range(runs)
    )

    per_criterion_stdev: dict[str, float] = {}
    for c in rubric.criteria:
        vals = [e.score_map()[c.id] for e in evals]
        per_criterion_stdev[c.id] = round(statistics.pstdev(vals), 4)

    totals = [e.weighted_total for e in evals]
    total_stdev = round(statistics.pstdev(totals), 6)
    total_spread = round(max(totals) - min(totals), 6)
    passes = {e.passed for e in evals}
    pass_flips = len(passes) > 1

    unstable = (
        total_stdev > max_total_stdev
        or any(s > max_criterion_stdev for s in per_criterion_stdev.values())
        or pass_flips
    )

    return ConsistencyReport(
        runs=runs,
        per_criterion_stdev=per_criterion_stdev,
        total_mean=round(statistics.fmean(totals), 6),
        total_stdev=total_stdev,
        total_spread=total_spread,
        pass_flips=pass_flips,
        unstable=unstable,
        evaluations=evals,
    )
