"""1회전 상태 기계 (PRD §8). 순수 로직.

온보딩 → 과제수령 → 자료탐색 → 1차작성 → 반려 → 재작업 → 완료
- 반려 루프(작성→반려→재작업)가 핵심(무기②③ 재료).
- max_revisions(기본 1, Q2)로 반려 횟수 제어. 통과 시 즉시 완료 가능.
"""
from __future__ import annotations

from enum import Enum


class State(str, Enum):
    ONBOARDING = "onboarding"
    TASK_RECEIVED = "task_received"
    EXPLORING = "exploring"
    DRAFTING = "drafting"
    UNDER_REVIEW = "under_review"
    REVISING = "revising"
    COMPLETED = "completed"


# 허용 전이 (이벤트 없는 순방향 골격)
_ALLOWED: dict[State, set[State]] = {
    State.ONBOARDING: {State.TASK_RECEIVED},
    State.TASK_RECEIVED: {State.EXPLORING, State.DRAFTING},
    State.EXPLORING: {State.DRAFTING},
    State.DRAFTING: {State.UNDER_REVIEW},
    State.UNDER_REVIEW: {State.REVISING, State.COMPLETED},
    State.REVISING: {State.UNDER_REVIEW},
    State.COMPLETED: set(),
}


class InvalidTransition(Exception):
    pass


def can_transition(src: State, dst: State) -> bool:
    return dst in _ALLOWED.get(src, set())


def assert_transition(src: State, dst: State) -> None:
    if not can_transition(src, dst):
        raise InvalidTransition(f"{src.value} → {dst.value} 불가")


def next_after_review(*, passed: bool, revisions_used: int, max_revisions: int) -> State:
    """심사 결과에 따른 다음 상태.

    - 통과 → 완료
    - 불통과 & 반려 여력 있음 → 재작업
    - 불통과 & 반려 소진 → 완료(미통과로 종료해도 무기는 생성: 과정·성장 서사가 핵심)
    """
    if passed:
        return State.COMPLETED
    if revisions_used < max_revisions:
        return State.REVISING
    return State.COMPLETED
