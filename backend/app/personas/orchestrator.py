"""세션 단위 페르소나 오케스트레이터.

한 세션의 3인(매니저/고객/엔지니어) 에이전트를 보유하고, 사용자가 지목한 인물에게 라우팅.
인물별 대화 히스토리는 독립(정보 비대칭 유지).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..llm.provider import LLMProvider
from .agent import PersonaAgent
from .loader import Persona, load_all_personas


@dataclass
class SessionPersonas:
    scenario_id: str
    provider: LLMProvider
    agents: dict[str, PersonaAgent] = field(default_factory=dict)

    @classmethod
    def create(cls, scenario_id: str, provider: LLMProvider) -> "SessionPersonas":
        personas: dict[str, Persona] = load_all_personas(scenario_id)
        agents = {pid: PersonaAgent(provider, p) for pid, p in personas.items()}
        return cls(scenario_id=scenario_id, provider=provider, agents=agents)

    def persona_ids(self) -> list[str]:
        return sorted(self.agents)

    def send(self, persona_id: str, message: str) -> str:
        if persona_id not in self.agents:
            raise KeyError(f"세션에 없는 페르소나: {persona_id}")
        return self.agents[persona_id].reply(message)

    def transcript(self, persona_id: str) -> list[dict[str, str]]:
        return list(self.agents[persona_id].history)
