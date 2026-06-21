"""FastAPI 엔트리 (P1-1 스켈레톤).

현재는 헬스체크 + 평가 엔드포인트(키 있을 때)만. 세션/페르소나/무기 라우트는 후속.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import GOLDEN_SETS_DIR, get_settings
from .evaluation.rubric import load_rubric
from .evaluation.scorer import score_submission
from .llm.provider import build_default_provider

app = FastAPI(title="FIELD — AX PM MVP", version="0.1")

_RUBRIC_PATH = GOLDEN_SETS_DIR / "ax-pm" / "rubric.json"


class EvaluateRequest(BaseModel):
    submission_text: str
    golden_text: str | None = None


@app.get("/health")
def health() -> dict[str, object]:
    s = get_settings()
    return {"status": "ok", "openai_configured": s.has_openai, "model": s.openai_model}


@app.post("/api/evaluate")
def evaluate(req: EvaluateRequest) -> dict[str, object]:
    settings = get_settings()
    if not settings.has_openai:
        raise HTTPException(503, "OPENAI_API_KEY 미설정 — 채점 불가")
    rubric = load_rubric(_RUBRIC_PATH)
    provider = build_default_provider(settings)
    ev = score_submission(provider, rubric, req.submission_text, req.golden_text)
    return {
        "rubric": f"{ev.rubric_id} v{ev.rubric_version}",
        "weighted_total": ev.weighted_total,
        "passed": ev.passed,
        "scores": [
            {"id": s.criterion_id, "score": s.score, "evidence": s.evidence}
            for s in ev.scores
        ],
        "overall_comment": ev.overall_comment,
    }
