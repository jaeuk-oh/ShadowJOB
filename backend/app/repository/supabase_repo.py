"""Supabase 세션 저장소.

테이블 `sessions(session_id text primary key, data jsonb)`를 사용한다.
supabase 패키지는 지연 임포트 → 키/패키지 없을 때 인메모리로 폴백 가능.
(라이브 검증은 키 추가 후. 데이터 계약은 to_dict/from_dict로 인메모리와 동일.)
"""
from __future__ import annotations

from ..session.model import SessionRecord
from .base import SessionNotFound

TABLE = "sessions"


class SupabaseSessionRepository:
    def __init__(self, url: str, service_key: str) -> None:
        from supabase import create_client  # 지연 임포트

        self._client = create_client(url, service_key)

    def save(self, record: SessionRecord) -> None:
        self._client.table(TABLE).upsert(
            {"session_id": record.session_id, "data": record.to_dict()}
        ).execute()

    def get(self, session_id: str) -> SessionRecord:
        res = (
            self._client.table(TABLE)
            .select("data")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        if not rows:
            raise SessionNotFound(session_id)
        return SessionRecord.from_dict(rows[0]["data"])

    def exists(self, session_id: str) -> bool:
        res = (
            self._client.table(TABLE)
            .select("session_id")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )
        return bool(res.data)
