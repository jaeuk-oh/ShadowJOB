"""인메모리 세션 저장소 (기본값·테스트용).

직렬화 라운드트립을 거쳐 저장 → Supabase 경로와 동일한 데이터 계약을 강제(저장 형태 검증).
"""
from __future__ import annotations

from ..session.model import SessionRecord
from .base import SessionNotFound


class InMemorySessionRepository:
    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def save(self, record: SessionRecord) -> None:
        # to_dict로 직렬화해 저장 → 영속화 계약과 동일하게 검증
        self._store[record.session_id] = record.to_dict()

    def get(self, session_id: str) -> SessionRecord:
        if session_id not in self._store:
            raise SessionNotFound(session_id)
        return SessionRecord.from_dict(self._store[session_id])

    def exists(self, session_id: str) -> bool:
        return session_id in self._store
