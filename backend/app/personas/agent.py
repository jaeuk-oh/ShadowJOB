"""PersonaAgent — 한 인물의 대화 상태를 들고 다음 발화를 생성."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..llm.provider import LLMProvider
from .loader import Persona

# 페르소나는 자연스러운 변주를 위해 채점(0.0)보다 높은 temperature
DEFAULT_PERSONA_TEMPERATURE = 0.7


@dataclass
class PersonaAgent:
    provider: LLMProvider
    persona: Persona
    temperature: float = DEFAULT_PERSONA_TEMPERATURE
    history: list[dict[str, str]] = field(default_factory=list)

    @property
    def persona_id(self) -> str:
        return self.persona.persona_id

    def reply(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        text = self.provider.complete_text(
            system=self.persona.system_prompt,
            messages=list(self.history),
            temperature=self.temperature,
        )
        self.history.append({"role": "assistant", "content": text})
        return text

    def inject_assistant(self, content: str) -> None:
        """매니저의 과제 전달 등 사용자 입력 없이 인물이 먼저 말한 발화 기록."""
        self.history.append({"role": "assistant", "content": content})
