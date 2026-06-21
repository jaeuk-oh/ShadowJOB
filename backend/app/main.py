"""FastAPI 엔트리 — 세션 서비스 라우트 마운트.

저장소·LLM 제공자 선택은 설정(환경변수) 기반:
- OPENAI_API_KEY 있으면 LLM 기능 활성, 없으면 해당 엔드포인트 503.
- SUPABASE_* 있으면 Supabase 저장소, 없으면 인메모리.
"""
from __future__ import annotations

from fastapi import FastAPI

from .api.routes import router
from .config import get_settings

app = FastAPI(title="FIELD — AX PM MVP", version="0.1")
app.include_router(router)


@app.get("/health")
def health() -> dict[str, object]:
    s = get_settings()
    return {
        "status": "ok",
        "openai_configured": s.has_openai,
        "model": s.openai_model,
        "supabase_configured": bool(s.supabase_url and s.supabase_service_key),
    }
