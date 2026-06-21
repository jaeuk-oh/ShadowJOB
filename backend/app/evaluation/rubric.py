"""루브릭 로딩 + 가중 점수 계산 (순수 로직, stdlib만 사용).

루브릭은 `golden-sets/<role>/rubric.json`에서 로드 → 코드 수정 없이 교체/버전업 가능.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Criterion:
    id: str
    name: str
    competencies: tuple[str, ...]
    weight: float
    anchors: dict[str, str]


@dataclass(frozen=True)
class Rubric:
    rubric_id: str
    version: str
    artifact_type: str
    scale_min: int
    scale_max: int
    pass_threshold: float
    criteria: tuple[Criterion, ...]

    @property
    def criterion_ids(self) -> tuple[str, ...]:
        return tuple(c.id for c in self.criteria)

    def criterion(self, cid: str) -> Criterion:
        for c in self.criteria:
            if c.id == cid:
                return c
        raise KeyError(cid)


def load_rubric(path: str | Path) -> Rubric:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    scale = data.get("scale", {"min": 0, "max": 4})
    criteria = tuple(
        Criterion(
            id=c["id"],
            name=c["name"],
            competencies=tuple(c.get("competencies", ())),
            weight=float(c["weight"]),
            anchors={str(k): v for k, v in c.get("anchors", {}).items()},
        )
        for c in data["criteria"]
    )
    rubric = Rubric(
        rubric_id=data["rubric_id"],
        version=str(data["version"]),
        artifact_type=data["artifact_type"],
        scale_min=int(scale.get("min", 0)),
        scale_max=int(scale.get("max", 4)),
        pass_threshold=float(data.get("pass_threshold", 0.7)),
        criteria=criteria,
    )
    _validate(rubric)
    return rubric


def _validate(rubric: Rubric) -> None:
    if not rubric.criteria:
        raise ValueError("루브릭에 criteria가 없습니다.")
    total_w = sum(c.weight for c in rubric.criteria)
    if abs(total_w - 1.0) > 1e-6:
        raise ValueError(f"criteria 가중치 합이 1.0이 아닙니다: {total_w}")
    if rubric.scale_max <= rubric.scale_min:
        raise ValueError("scale_max는 scale_min보다 커야 합니다.")


def normalized_weighted_score(scores: dict[str, int], rubric: Rubric) -> float:
    """항목별 원점수(scale_min~scale_max)를 가중 평균해 0..1로 정규화."""
    span = rubric.scale_max - rubric.scale_min
    total = 0.0
    for c in rubric.criteria:
        if c.id not in scores:
            raise ValueError(f"채점 누락 항목: {c.id}")
        raw = scores[c.id]
        if not (rubric.scale_min <= raw <= rubric.scale_max):
            raise ValueError(f"{c.id} 점수 범위 위반: {raw}")
        total += c.weight * ((raw - rubric.scale_min) / span)
    return round(total, 6)


def passed(scores: dict[str, int], rubric: Rubric) -> bool:
    return normalized_weighted_score(scores, rubric) >= rubric.pass_threshold
