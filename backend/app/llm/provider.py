"""LLM 제공자 추상화.

핵심 설계: LLM 호출을 인터페이스 뒤로 숨긴다.
- 평가 엔진·페르소나는 `LLMProvider`에만 의존 → 테스트는 mock으로 결정적 검증(라이브 콜 불필요).
- 실서비스는 `OpenAIProvider`(Structured Outputs로 JSON 강제).
- 모델/키는 config(환경변수)로 분리 → 교체 용이.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Protocol


class LLMProvider(Protocol):
    """JSON 스키마에 맞는 구조화 출력을 반환하는 최소 인터페이스."""

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: dict[str, Any],
        schema_name: str = "response",
        temperature: float | None = None,
    ) -> dict[str, Any]:
        ...


class OpenAIProvider:
    """OpenAI 구현. Structured Outputs(json_schema)로 스키마 준수를 강제한다.

    openai 패키지는 지연 임포트 → 테스트/스캐폴드 환경에서 미설치여도 무방.
    """

    def __init__(self, *, api_key: str, model: str, temperature: float = 0.0) -> None:
        self.model = model
        self.temperature = temperature
        from openai import OpenAI  # 지연 임포트

        self._client = OpenAI(api_key=api_key)

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: dict[str, Any],
        schema_name: str = "response",
        temperature: float | None = None,
    ) -> dict[str, Any]:
        resp = self._client.chat.completions.create(
            model=self.model,
            temperature=self.temperature if temperature is None else temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                },
            },
        )
        content = resp.choices[0].message.content or "{}"
        return json.loads(content)


class MockProvider:
    """테스트용. 호출마다 `responder(system, user)`가 돌려주는 dict를 반환.

    채점 일관성 하니스 테스트를 위해 호출 횟수를 기록한다.
    """

    def __init__(self, responder: Callable[[str, str], dict[str, Any]]) -> None:
        self._responder = responder
        self.calls: list[tuple[str, str]] = []

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: dict[str, Any],
        schema_name: str = "response",
        temperature: float | None = None,
    ) -> dict[str, Any]:
        self.calls.append((system, user))
        return self._responder(system, user)


def build_default_provider(settings: Any) -> LLMProvider:
    """config.Settings로부터 실제 제공자 생성. 키 없으면 명확히 에러."""
    if not getattr(settings, "openai_api_key", None):
        raise RuntimeError(
            "OPENAI_API_KEY가 없습니다. 라이브 LLM 제공자를 만들 수 없습니다 "
            "(테스트는 MockProvider 사용)."
        )
    return OpenAIProvider(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=settings.openai_temperature,
    )
