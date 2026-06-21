"""FastAPI 라우트 — 세션 서비스 노출 (배선).

정적/비LLM 엔드포인트(시나리오·세션 생성·조회·의사결정)는 키 없이 동작.
LLM 필요 엔드포인트(chat·submit·weapons)는 키 없으면 503.
저장소는 프로세스 단일 인스턴스(설정상 Supabase면 Supabase).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config import GOLDEN_SETS_DIR, get_settings
from ..evaluation.rubric import load_rubric
from ..repository.base import SessionNotFound
from ..repository.factory import get_repository
from ..services.session_service import SessionService

router = APIRouter(prefix="/api")

_settings = get_settings()
_repo = get_repository(_settings)
_rubric = load_rubric(GOLDEN_SETS_DIR / "ax-pm" / "rubric.json")
_golden = (GOLDEN_SETS_DIR / "ax-pm" / "golden-01-strong.md").read_text(encoding="utf-8")
_diagnosis_rubric = load_rubric(GOLDEN_SETS_DIR / "ax-pm" / "diagnosis-rubric.json")


class _NullProvider:
    def complete_json(self, **kw: Any) -> dict[str, Any]:
        raise RuntimeError("LLM 미설정")

    def complete_text(self, **kw: Any) -> str:
        raise RuntimeError("LLM 미설정")


def _base_service() -> SessionService:
    """비LLM 작업용(provider 미사용)."""
    return SessionService(
        provider=_NullProvider(), repository=_repo, rubric=_rubric, golden_text=_golden
    )


def _llm_service() -> SessionService:
    """LLM 작업용. 키 없으면 503."""
    if not _settings.has_openai:
        raise HTTPException(503, "OPENAI_API_KEY 미설정 — LLM 기능 사용 불가")
    from ..llm.provider import build_default_provider

    return SessionService(
        provider=build_default_provider(_settings),
        repository=_repo,
        rubric=_rubric,
        golden_text=_golden,
    )


def _require(session_getter):
    try:
        return session_getter()
    except SessionNotFound:
        raise HTTPException(404, "세션 없음")


# ---------- 요청 모델 ----------
class CreateSessionReq(BaseModel):
    scenario_id: str = "saver-studio"
    max_revisions: int = 1


class DecisionReq(BaseModel):
    note: str


class ChatReq(BaseModel):
    persona_id: str
    message: str


class SubmitReq(BaseModel):
    text: str


class SurveyReq(BaseModel):
    star_self_report: bool
    comment: str = ""


class BlindEvalReq(BaseModel):
    looks_real: bool
    evaluator: str = ""
    comment: str = ""


class DiagnoseReq(BaseModel):
    resume_text: str


# ---------- 시나리오 ----------
@router.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: str) -> dict[str, Any]:
    try:
        b = _base_service().get_scenario(scenario_id)
    except FileNotFoundError:
        raise HTTPException(404, "시나리오 없음")
    return {
        "scenario_id": b.scenario_id,
        "background": b.background,
        "task_message": b.task_message,
        "personas": [
            {"persona_id": p.persona_id, "name": p.name, "role": p.role} for p in b.personas
        ],
        "assets": {"cs_logs_csv": b.cs_logs_csv, "dashboard_md": b.dashboard_md},
        "brief_template": b.brief_template,
    }


# ---------- 진단·개인화 앞단 퍼널 (P1.5) ----------
@router.post("/diagnose")
def diagnose(req: DiagnoseReq) -> dict[str, Any]:
    svc = _llm_service()
    if not req.resume_text.strip():
        raise HTTPException(400, "이력서/포폴 텍스트가 비어 있습니다")
    rep = svc.diagnose_resume(req.resume_text, _diagnosis_rubric)
    return {
        "rubric": f"{rep.rubric_id} v{rep.rubric_version}",
        "weighted_total": rep.weighted_total,
        "meets_bar": rep.meets_bar,
        "scores": [
            {"id": s.criterion_id, "score": s.score, "evidence": s.evidence}
            for s in rep.scores
        ],
        "gaps": [
            {"id": g.criterion_id, "score": g.score, "evidence": g.evidence}
            for g in rep.gaps
        ],
        "recommended_focus": [
            {"id": f.criterion_id, "area": f.area, "message": f.message}
            for f in rep.recommended_focus
        ],
        "summary": rep.summary,
    }


# ---------- 세션 ----------
def _session_view(rec) -> dict[str, Any]:
    return {
        "session_id": rec.session_id,
        "scenario_id": rec.scenario_id,
        "state": rec.state.value,
        "submissions": len(rec.submissions),
        "revisions_used": rec.revisions_used,
        "completed": rec.is_completed,
        "passed": rec.passed,
        "rejections": rec.rejections,
    }


@router.post("/sessions")
def create_session(req: CreateSessionReq) -> dict[str, Any]:
    svc = _base_service()
    rec = svc.create_session(req.scenario_id, max_revisions=req.max_revisions)
    return _session_view(rec)


@router.get("/sessions/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    rec = _require(lambda: _base_service().get_session(session_id))
    return _session_view(rec)


@router.post("/sessions/{session_id}/decisions")
def add_decision(session_id: str, req: DecisionReq) -> dict[str, Any]:
    _require(lambda: _base_service().get_session(session_id))
    _base_service().record_decision(session_id, req.note)
    return {"ok": True}


@router.post("/sessions/{session_id}/chat")
def chat(session_id: str, req: ChatReq) -> dict[str, Any]:
    svc = _llm_service()
    _require(lambda: svc.get_session(session_id))
    try:
        reply = svc.chat(session_id, req.persona_id, req.message)
    except FileNotFoundError:
        raise HTTPException(404, "페르소나 없음")
    return {"persona_id": req.persona_id, "reply": reply}


@router.post("/sessions/{session_id}/submit")
def submit(session_id: str, req: SubmitReq) -> dict[str, Any]:
    svc = _llm_service()
    _require(lambda: svc.get_session(session_id))
    res = svc.submit(session_id, req.text)
    ev = res.evaluation
    return {
        "state": res.state,
        "rejection": res.rejection,
        "evaluation": {
            "weighted_total": ev.weighted_total,
            "passed": ev.passed,
            "scores": [
                {"id": s.criterion_id, "score": s.score, "evidence": s.evidence}
                for s in ev.scores
            ],
            "overall_comment": ev.overall_comment,
        },
    }


# ---------- 베타 계측 (P1-23) ----------
@router.post("/sessions/{session_id}/survey")
def survey(session_id: str, req: SurveyReq) -> dict[str, Any]:
    svc = _base_service()
    _require(lambda: svc.get_session(session_id))
    svc.record_survey(session_id, req.star_self_report, req.comment)
    return {"ok": True}


@router.post("/sessions/{session_id}/blind-eval")
def blind_eval(session_id: str, req: BlindEvalReq) -> dict[str, Any]:
    svc = _base_service()
    _require(lambda: svc.get_session(session_id))
    svc.record_blind_eval(session_id, req.looks_real, req.evaluator, req.comment)
    return {"ok": True}


@router.get("/metrics")
def metrics() -> dict[str, Any]:
    return _base_service().metrics()


@router.get("/sessions/{session_id}/weapons")
def weapons(session_id: str) -> dict[str, Any]:
    svc = _llm_service()
    rec = _require(lambda: svc.get_session(session_id))
    if not rec.is_completed:
        raise HTTPException(409, "세션이 완료되지 않음")
    pkg = svc.get_weapons(session_id)
    return {
        "document_artifact": pkg.document_artifact,
        "star_arsenal": pkg.star_arsenal,
        "process_record": pkg.process_record,
    }
