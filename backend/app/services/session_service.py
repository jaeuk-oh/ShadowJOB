"""세션 서비스 — 배선 계층.

저장소(SessionRepository) + LLM(LLMProvider) + 평가/페르소나/무기 모듈을 묶어
프론트가 호출할 유스케이스를 제공한다. 흐름은 상태 기계(PRD §8)를 따른다.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from ..evaluation.rubric import Rubric
from ..evaluation.scorer import Evaluation, score_submission
from ..llm.provider import LLMProvider
from ..personas.agent import PersonaAgent
from ..personas.feedback import build_manager_feedback
from ..personas.loader import load_persona
from ..repository.base import SessionRepository
from ..scenario.loader import ScenarioBundle, load_scenario
from ..session.model import SessionRecord
from ..session.state import State
from ..weapons.generator import WeaponPackage, generate_package

MANAGER_PERSONA_ID = "manager-kim-dohyun"


@dataclass
class SubmitResult:
    state: str
    evaluation: Evaluation
    rejection: str | None


class SessionService:
    def __init__(
        self,
        *,
        provider: LLMProvider,
        repository: SessionRepository,
        rubric: Rubric,
        golden_text: str | None = None,
    ) -> None:
        self.provider = provider
        self.repo = repository
        self.rubric = rubric
        self.golden_text = golden_text

    # ---------- 시나리오 (정적, 비노출 제거됨) ----------
    def get_scenario(self, scenario_id: str) -> ScenarioBundle:
        return load_scenario(scenario_id)

    # ---------- 진단·개인화 앞단 퍼널 (P1.5) ----------
    def diagnose_resume(self, resume_text: str, diagnosis_rubric: Rubric):
        from ..diagnosis.diagnose import diagnose

        return diagnose(self.provider, diagnosis_rubric, resume_text)

    # ---------- 세션 ----------
    def create_session(self, scenario_id: str, *, max_revisions: int = 1) -> SessionRecord:
        rec = SessionRecord(
            session_id=uuid.uuid4().hex,
            scenario_id=scenario_id,
            max_revisions=max_revisions,
        )
        rec.receive_task()  # 온보딩 → 과제수령
        self.repo.save(rec)
        return rec

    def get_session(self, session_id: str) -> SessionRecord:
        return self.repo.get(session_id)

    def record_decision(self, session_id: str, note: str) -> None:
        rec = self.repo.get(session_id)
        rec.record_decision(note)
        self.repo.save(rec)

    # ---------- 베타 계측 (P1-23) ----------
    def record_survey(self, session_id: str, star_self_report: bool, comment: str = "") -> None:
        rec = self.repo.get(session_id)
        rec.record_survey(star_self_report, comment)
        self.repo.save(rec)

    def record_blind_eval(
        self, session_id: str, looks_real: bool, evaluator: str = "", comment: str = ""
    ) -> None:
        rec = self.repo.get(session_id)
        rec.record_blind_eval(looks_real, evaluator, comment)
        self.repo.save(rec)

    def metrics(self) -> dict:
        from ..metrics import compute_metrics

        return compute_metrics(self.repo.list_all())

    # ---------- 페르소나 대화 ----------
    def chat(self, session_id: str, persona_id: str, message: str) -> str:
        rec = self.repo.get(session_id)
        persona = load_persona(rec.scenario_id, persona_id)
        agent = PersonaAgent(self.provider, persona)
        agent.history = list(rec.persona_histories.get(persona_id, []))
        reply = agent.reply(message)
        rec.persona_histories[persona_id] = agent.history
        # 탐색 진입 표시(자료/대화 시작) — 상태가 과제수령이면 탐색으로
        if rec.state == State.TASK_RECEIVED:
            rec.start_exploring()
        self.repo.save(rec)
        return reply

    # ---------- 제출 → 채점 → (반려) ----------
    def submit(self, session_id: str, text: str) -> SubmitResult:
        rec = self.repo.get(session_id)
        if rec.state in (State.TASK_RECEIVED, State.EXPLORING):
            rec.start_drafting()
        rec.submit(text)  # → UNDER_REVIEW
        evaluation = score_submission(self.provider, self.rubric, text, self.golden_text)

        rejection: str | None = None
        # 반려 예정이면 매니저 피드백 생성
        from ..session.state import next_after_review

        will_revise = next_after_review(
            passed=evaluation.passed,
            revisions_used=rec.revisions_used,
            max_revisions=rec.max_revisions,
        ) == State.REVISING
        if will_revise:
            manager = load_persona(rec.scenario_id, MANAGER_PERSONA_ID)
            rejection = build_manager_feedback(self.provider, manager, evaluation, self.rubric)

        rec.apply_review(evaluation, rejection_message=rejection)
        self.repo.save(rec)
        return SubmitResult(state=rec.state.value, evaluation=evaluation, rejection=rejection)

    # ---------- 무기 ----------
    def get_weapons(self, session_id: str) -> WeaponPackage:
        rec = self.repo.get(session_id)
        return generate_package(self.provider, rec)
