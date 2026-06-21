"""시나리오 자산 로더 (P1-3).

scenario.md / dashboard 에는 '정답 키·채점용' 비노출 섹션이 있다 → 반드시 제거 후 노출.
사용자에게는 배경 · 매니저 과제 · 페르소나(이름/역할) · 자료(CSV·대시보드) · Brief 템플릿만 제공.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..config import SCENARIOS_DIR
from ..personas.loader import list_persona_ids

# 이 마커가 제목에 들어간 섹션은 사용자 비노출
HIDDEN_MARKERS = ("정답 키", "비노출", "역량모델 매핑")


@dataclass(frozen=True)
class PersonaInfo:
    persona_id: str
    name: str
    role: str


@dataclass(frozen=True)
class ScenarioBundle:
    scenario_id: str
    background: str
    task_message: str
    personas: tuple[PersonaInfo, ...]
    cs_logs_csv: str
    dashboard_md: str
    brief_template: str


_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def strip_hidden_sections(md: str, markers: tuple[str, ...] = HIDDEN_MARKERS) -> str:
    """제목에 marker가 포함된 섹션을, 같은/상위 레벨 제목이 나올 때까지 제거."""
    out: list[str] = []
    skip_level = 0  # 0이면 스킵 아님
    for line in md.splitlines():
        m = _HEADING.match(line)
        if m:
            level = len(m.group(1))
            title = m.group(2)
            if skip_level and level <= skip_level:
                skip_level = 0  # 스킵 종료, 이 제목은 다시 평가
            if not skip_level and any(mk in title for mk in markers):
                skip_level = level
                continue
        if skip_level:
            continue
        out.append(line)
    return "\n".join(out).strip()


def _section(md: str, title_contains: str) -> str:
    """'## 제목' 섹션 본문(다음 동일레벨 제목 전까지)을 반환."""
    lines = md.splitlines()
    start = None
    start_level = 0
    for i, line in enumerate(lines):
        m = _HEADING.match(line)
        if m and title_contains in m.group(2):
            start = i + 1
            start_level = len(m.group(1))
            break
    if start is None:
        return ""
    body = []
    for line in lines[start:]:
        m = _HEADING.match(line)
        if m and len(m.group(1)) <= start_level:
            break
        body.append(line)
    return "\n".join(body).strip()


def _manager_quote(md: str) -> str:
    """'## 과제 정의' 내 매니저 인용(>로 시작하는 블록)만 추출."""
    section = _section(md, "과제 정의")
    quote = [ln[1:].strip() for ln in section.splitlines() if ln.strip().startswith(">")]
    return "\n".join(quote).strip()


def _persona_role(card: str) -> str:
    m = re.search(r"#\s*페르소나\s*[—\-]\s*[^()\n]+\(([^)]*)\)", card)
    return m.group(1).strip() if m else ""


def load_scenario(scenario_id: str) -> ScenarioBundle:
    base = SCENARIOS_DIR / scenario_id
    scenario_md = (base / "scenario.md").read_text(encoding="utf-8")
    dashboard_md = (base / "assets" / "dashboard-metrics.md").read_text(encoding="utf-8")
    cs_logs = (base / "assets" / "cs-logs.csv").read_text(encoding="utf-8")
    brief_template = (base / "task-brief-template.md").read_text(encoding="utf-8")

    personas = []
    for pid in list_persona_ids(scenario_id):
        card = (base / "personas" / f"{pid}.md").read_text(encoding="utf-8")
        name_m = re.search(r"#\s*페르소나\s*[—\-]\s*([^()\n]+)", card)
        name = name_m.group(1).strip() if name_m else pid
        personas.append(PersonaInfo(persona_id=pid, name=name, role=_persona_role(card)))

    return ScenarioBundle(
        scenario_id=scenario_id,
        background=_section(scenario_md, "배경"),
        task_message=_manager_quote(scenario_md),
        personas=tuple(personas),
        cs_logs_csv=cs_logs,
        dashboard_md=strip_hidden_sections(dashboard_md),
        brief_template=brief_template,
    )
