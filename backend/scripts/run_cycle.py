"""P0-4 전체 1회전 데모 — 무기 3종이 실제로 뽑히는지 확인. (OPENAI_API_KEY 필요)

흐름: 세션 생성 → (약한 1차 제출 → 채점/반려 → 골든 재작업 제출 → 통과) → 무기 3종 생성·출력.
약한/강한 산출물은 golden-sets의 예시 파일을 사용(실사용에선 사용자가 직접 작성).

사용:
  python scripts/run_cycle.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import GOLDEN_SETS_DIR, get_settings  # noqa: E402
from app.evaluation.rubric import load_rubric  # noqa: E402
from app.evaluation.scorer import score_submission  # noqa: E402
from app.llm.provider import build_default_provider  # noqa: E402
from app.personas.feedback import build_manager_feedback  # noqa: E402
from app.personas.loader import load_persona  # noqa: E402
from app.session.model import SessionRecord  # noqa: E402
from app.session.state import State  # noqa: E402
from app.weapons.generator import generate_package  # noqa: E402

SCENARIO = "saver-studio"


def main() -> int:
    settings = get_settings()
    if not settings.has_openai:
        print("OPENAI_API_KEY가 없습니다. .env 설정 후 실행하세요.", file=sys.stderr)
        return 2

    provider = build_default_provider(settings)
    rubric = load_rubric(GOLDEN_SETS_DIR / "ax-pm" / "rubric.json")
    golden = (GOLDEN_SETS_DIR / "ax-pm" / "golden-01-strong.md").read_text(encoding="utf-8")
    weak = (GOLDEN_SETS_DIR / "ax-pm" / "example-weak-draft.md").read_text(encoding="utf-8")
    manager = load_persona(SCENARIO, "manager-kim-dohyun")

    s = SessionRecord(session_id="demo", scenario_id=SCENARIO, max_revisions=1)
    s.receive_task(); s.start_exploring(); s.start_drafting()
    s.record_decision("환불 미해결인데 응답시간이 빨라 인프라가 아닌 지식베이스 문제로 가설을 세움")

    # 1차(약한) 제출 → 채점 → 반려
    s.submit(weak)
    ev1 = score_submission(provider, rubric, weak, golden)
    print(f"[1차 채점] 총점={ev1.weighted_total} {'PASS' if ev1.passed else 'FAIL'}")
    if s.state == State.UNDER_REVIEW and not ev1.passed:
        rej = build_manager_feedback(provider, manager, ev1, rubric)
        s.apply_review(ev1, rejection_message=rej)
        print(f"[매니저 반려] {rej}\n")

    # 2차(강한) 재작업 제출 → 채점 → 통과
    if s.state == State.REVISING:
        s.submit(golden)
        ev2 = score_submission(provider, rubric, golden, golden)
        print(f"[2차 채점] 총점={ev2.weighted_total} {'PASS' if ev2.passed else 'FAIL'}")
        s.apply_review(ev2)

    print(f"[세션 종료 상태] {s.state.value}\n")

    # 무기 3종 추출
    pkg = generate_package(provider, s)
    print("=" * 60)
    print("무기 ① 증거형 (서류 산출물)\n")
    print(pkg.document_artifact[:800])
    print("\n" + "=" * 60)
    print("무기 ② 서사형 (면접 STAR + 예상질문)\n")
    print(json.dumps(pkg.star_arsenal, ensure_ascii=False, indent=2)[:1200])
    print("\n" + "=" * 60)
    print("무기 ③ 신뢰형 (과정 기록)\n")
    print(pkg.process_record[:1200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
