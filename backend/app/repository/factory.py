"""설정에 따라 저장소 선택. Supabase 키 있으면 Supabase, 없으면 인메모리."""
from __future__ import annotations

from typing import Any

from .base import SessionRepository
from .memory import InMemorySessionRepository


def get_repository(settings: Any) -> SessionRepository:
    url = getattr(settings, "supabase_url", None)
    key = getattr(settings, "supabase_service_key", None)
    if url and key:
        from .supabase_repo import SupabaseSessionRepository

        return SupabaseSessionRepository(url, key)
    return InMemorySessionRepository()
