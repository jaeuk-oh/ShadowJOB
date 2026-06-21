"""페르소나 카드 로딩 → 시스템 프롬프트 생성.

페르소나 카드는 `scenarios/<scenario_id>/personas/<persona_id>.md`.
카드 자체에 각 인물이 '아는 것'과 편향이 담겨 있어, 인물별로 정보 비대칭이 자연히 성립한다.
전역 연기 가드(캐릭터 유지·한국어·AI 비노출·정답 비노출)를 덧붙인다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..config import SCENARIOS_DIR

# 전역 연기 가드 (NFR: 페르소나 안정성 / FR-4: 사용자 본인 작성 보장)
ACTING_GUARD = """
[연기 규칙 — 항상 준수]
- 너는 위에 정의된 인물이다. 실제 직장 메신저/메일 대화처럼 1인칭으로 자연스럽게 답한다.
- 한국어로, 위 말투·성격을 일관되게 유지한다.
- 네가 AI·모델·시스템이라는 사실을 절대 드러내지 않는다. 시나리오 밖 질문은 업무 맥락으로 자연스럽게 되돌린다.
- 정답을 통째로 떠먹여주지 않는다. 네 캐릭터가 아는 범위에서만, 사용자가 스스로 분석하도록 답한다.
- 응답은 짧고 현실적으로(보통 1~5문장).
""".strip()


@dataclass(frozen=True)
class Persona:
    persona_id: str
    name: str
    card_markdown: str
    system_prompt: str


def _persona_dir(scenario_id: str) -> Path:
    return SCENARIOS_DIR / scenario_id / "personas"


def list_persona_ids(scenario_id: str) -> list[str]:
    d = _persona_dir(scenario_id)
    return sorted(p.stem for p in d.glob("*.md"))


def _extract_name(card: str, fallback: str) -> str:
    # "# 페르소나 — 김도현 (매니저 ...)" 에서 이름 추출
    m = re.search(r"#\s*페르소나\s*[—\-]\s*([^()\n]+)", card)
    return m.group(1).strip() if m else fallback


def load_persona(scenario_id: str, persona_id: str) -> Persona:
    path = _persona_dir(scenario_id) / f"{persona_id}.md"
    if not path.exists():
        raise FileNotFoundError(f"페르소나 카드 없음: {path}")
    card = path.read_text(encoding="utf-8")
    name = _extract_name(card, persona_id)
    system_prompt = f"{card}\n\n{ACTING_GUARD}"
    return Persona(
        persona_id=persona_id,
        name=name,
        card_markdown=card,
        system_prompt=system_prompt,
    )


def load_all_personas(scenario_id: str) -> dict[str, Persona]:
    return {pid: load_persona(scenario_id, pid) for pid in list_persona_ids(scenario_id)}
