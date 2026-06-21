"""환경 설정. LLM/Supabase 키는 환경변수로 분리(업데이트 친화)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# 레포 루트 (backend/app/config.py -> backend -> repo root)
REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIOS_DIR = REPO_ROOT / "scenarios"
GOLDEN_SETS_DIR = REPO_ROOT / "golden-sets"
COMPETENCY_DIR = REPO_ROOT / "competency-model"


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1")
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))
    supabase_url: str | None = os.getenv("SUPABASE_URL")
    supabase_service_key: str | None = os.getenv("SUPABASE_SERVICE_KEY")

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)


def get_settings() -> Settings:
    return Settings()
