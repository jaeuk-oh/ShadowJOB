"""세션 저장소 추상화. LLM 제공자와 동일 패턴 — 인터페이스 뒤로 숨겨 테스트는 인메모리로."""
from __future__ import annotations

from typing import Protocol

from ..session.model import SessionRecord


class SessionRepository(Protocol):
    def save(self, record: SessionRecord) -> None: ...
    def get(self, session_id: str) -> SessionRecord: ...
    def exists(self, session_id: str) -> bool: ...
    def list_all(self) -> list[SessionRecord]: ...  # 베타 계측 집계용


class SessionNotFound(Exception):
    pass
