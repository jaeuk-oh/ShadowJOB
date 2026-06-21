"""세션 레코드 — 1회전 동안 생성되는 모든 산출물·이력 보관 (순수 로직).

무기 3종의 재료가 여기 다 모인다:
- submissions: 회차별 제출본 (before→after / 무기①③)
- evaluations: 회차별 채점 (반려 근거)
- rejections: 매니저 반려 메시지
- decision_logs: 사용자의 판단 근거 (무기③)
- 페르소나 transcript는 오케스트레이터가 보유(필요 시 주입)

영속화(Supabase)는 이 구조를 그대로 직렬화한다(P1-2). 지금은 인메모리.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from typing import Any

from ..evaluation.scorer import CriterionScore, Evaluation
from .state import (
    State,
    assert_transition,
    next_after_review,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Submission:
    round: int
    text: str
    created_at: str = field(default_factory=_now)


@dataclass
class DecisionLogEntry:
    note: str
    created_at: str = field(default_factory=_now)


@dataclass
class SessionRecord:
    session_id: str
    scenario_id: str
    artifact_type: str = "problem_brief"
    max_revisions: int = 1  # Q2 기본값
    state: State = State.ONBOARDING

    submissions: list[Submission] = field(default_factory=list)
    evaluations: list[Evaluation] = field(default_factory=list)
    rejections: list[str] = field(default_factory=list)
    decision_logs: list[DecisionLogEntry] = field(default_factory=list)
    # 페르소나별 대화 히스토리 (정보 비대칭 유지, 영속화 대상)
    persona_histories: dict[str, list[dict[str, str]]] = field(default_factory=dict)

    # --- 베타 계측 (P1-23) ---
    created_at: str = field(default_factory=_now)
    events: list[dict[str, str]] = field(default_factory=list)  # {type, at} 전이/이벤트 로그
    survey_star_self_report: bool | None = None  # "STAR로 말할 수 있다" 자가응답
    survey_comment: str = ""
    blind_evals: list[dict[str, Any]] = field(default_factory=list)  # 담당자 블라인드 평가

    # --- 직렬화 (Supabase/JSON 영속화용) ---
    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "scenario_id": self.scenario_id,
            "artifact_type": self.artifact_type,
            "max_revisions": self.max_revisions,
            "state": self.state.value,
            "submissions": [vars(s) for s in self.submissions],
            "evaluations": [_eval_to_dict(e) for e in self.evaluations],
            "rejections": list(self.rejections),
            "decision_logs": [vars(d) for d in self.decision_logs],
            "persona_histories": self.persona_histories,
            "created_at": self.created_at,
            "events": self.events,
            "survey_star_self_report": self.survey_star_self_report,
            "survey_comment": self.survey_comment,
            "blind_evals": self.blind_evals,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionRecord":
        rec = cls(
            session_id=data["session_id"],
            scenario_id=data["scenario_id"],
            artifact_type=data.get("artifact_type", "problem_brief"),
            max_revisions=int(data.get("max_revisions", 1)),
            state=State(data.get("state", State.ONBOARDING.value)),
        )
        rec.submissions = [Submission(**s) for s in data.get("submissions", [])]
        rec.evaluations = [_eval_from_dict(e) for e in data.get("evaluations", [])]
        rec.rejections = list(data.get("rejections", []))
        rec.decision_logs = [DecisionLogEntry(**d) for d in data.get("decision_logs", [])]
        rec.persona_histories = data.get("persona_histories", {})
        if data.get("created_at"):
            rec.created_at = data["created_at"]
        rec.events = list(data.get("events", []))
        rec.survey_star_self_report = data.get("survey_star_self_report")
        rec.survey_comment = data.get("survey_comment", "")
        rec.blind_evals = list(data.get("blind_evals", []))
        return rec

    # --- 상태 전이 ---
    def transition(self, dst: State) -> None:
        assert_transition(self.state, dst)
        self.state = dst
        self.events.append({"type": f"state:{dst.value}", "at": _now()})

    # --- 진행 액션 ---
    def receive_task(self) -> None:
        self.transition(State.TASK_RECEIVED)

    def start_exploring(self) -> None:
        self.transition(State.EXPLORING)

    def start_drafting(self) -> None:
        # 탐색을 건너뛰고 바로 작성도 허용(상태 기계가 판단)
        self.transition(State.DRAFTING)

    def submit(self, text: str) -> Submission:
        """현재 작성/재작업 상태에서 제출 → 심사 대기로."""
        if self.state not in (State.DRAFTING, State.REVISING):
            from .state import InvalidTransition

            raise InvalidTransition(f"제출 불가 상태: {self.state.value}")
        sub = Submission(round=len(self.submissions) + 1, text=text)
        self.submissions.append(sub)
        self.transition(State.UNDER_REVIEW)
        return sub

    def record_decision(self, note: str) -> None:
        self.decision_logs.append(DecisionLogEntry(note=note))

    # --- 베타 계측 입력 ---
    def record_survey(self, star_self_report: bool, comment: str = "") -> None:
        """종료 설문: 이 경험을 면접에서 STAR로 말할 수 있겠는가."""
        self.survey_star_self_report = star_self_report
        self.survey_comment = comment
        self.events.append({"type": "survey", "at": _now()})

    def record_blind_eval(self, looks_real: bool, evaluator: str = "", comment: str = "") -> None:
        """채용 담당자 블라인드 평가: '진짜 실무자 결과물 같다'."""
        self.blind_evals.append(
            {"looks_real": looks_real, "evaluator": evaluator, "comment": comment, "at": _now()}
        )

    @property
    def revisions_used(self) -> int:
        # 1차 제출 이후의 추가 제출 수 = 반려 후 재작업 횟수
        return max(0, len(self.submissions) - 1)

    def apply_review(self, evaluation: Evaluation, rejection_message: str | None = None) -> State:
        """심사 결과 반영 → 다음 상태로. 반려면 매니저 메시지 보관."""
        if self.state != State.UNDER_REVIEW:
            from .state import InvalidTransition

            raise InvalidTransition("심사 상태가 아님")
        self.evaluations.append(evaluation)
        dst = next_after_review(
            passed=evaluation.passed,
            revisions_used=self.revisions_used,
            max_revisions=self.max_revisions,
        )
        if dst == State.REVISING and rejection_message is not None:
            self.rejections.append(rejection_message)
        self.transition(dst)
        return dst

    # --- 조회 ---
    @property
    def final_submission(self) -> Submission | None:
        return self.submissions[-1] if self.submissions else None

    @property
    def first_submission(self) -> Submission | None:
        return self.submissions[0] if self.submissions else None

    @property
    def is_completed(self) -> bool:
        return self.state == State.COMPLETED

    @property
    def passed(self) -> bool:
        return bool(self.evaluations) and self.evaluations[-1].passed

    @property
    def completed_at(self) -> str | None:
        for ev in reversed(self.events):
            if ev["type"] == f"state:{State.COMPLETED.value}":
                return ev["at"]
        return None


def _eval_to_dict(e: Evaluation) -> dict[str, Any]:
    return {
        "rubric_id": e.rubric_id,
        "rubric_version": e.rubric_version,
        "scores": [vars(s) for s in e.scores],
        "weighted_total": e.weighted_total,
        "passed": e.passed,
        "overall_comment": e.overall_comment,
    }


def _eval_from_dict(d: dict[str, Any]) -> Evaluation:
    return Evaluation(
        rubric_id=d["rubric_id"],
        rubric_version=d["rubric_version"],
        scores=tuple(CriterionScore(**s) for s in d.get("scores", [])),
        weighted_total=d["weighted_total"],
        passed=d["passed"],
        overall_comment=d.get("overall_comment", ""),
    )
