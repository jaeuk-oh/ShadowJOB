"""P0-3 수동 채점 CLI.

골든셋/약한초안/실제 산출물을 루브릭으로 채점한다. (OPENAI_API_KEY 필요)
일관성 측정도 가능 → H3 검증.

사용:
  python scripts/score_brief.py ../golden-sets/ax-pm/golden-01-strong.md
  python scripts/score_brief.py SUB.md --golden ../golden-sets/ax-pm/golden-01-strong.md --consistency 5
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import GOLDEN_SETS_DIR, get_settings  # noqa: E402
from app.evaluation.consistency import measure_consistency  # noqa: E402
from app.evaluation.rubric import load_rubric  # noqa: E402
from app.evaluation.scorer import score_submission  # noqa: E402
from app.llm.provider import build_default_provider  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("submission", help="채점할 산출물 파일(.md/.txt)")
    ap.add_argument("--rubric", default=str(GOLDEN_SETS_DIR / "ax-pm" / "rubric.json"))
    ap.add_argument("--golden", default=None, help="모범답안 파일(척도 정박용)")
    ap.add_argument("--consistency", type=int, default=0, help="N>=2면 일관성 측정")
    args = ap.parse_args()

    settings = get_settings()
    if not settings.has_openai:
        print("OPENAI_API_KEY가 없습니다. .env 설정 후 다시 실행하세요.", file=sys.stderr)
        return 2

    rubric = load_rubric(args.rubric)
    submission = Path(args.submission).read_text(encoding="utf-8")
    golden = Path(args.golden).read_text(encoding="utf-8") if args.golden else None
    provider = build_default_provider(settings)

    if args.consistency >= 2:
        rep = measure_consistency(provider, rubric, submission, golden, runs=args.consistency)
        print(f"[일관성] runs={rep.runs} total_mean={rep.total_mean} "
              f"total_stdev={rep.total_stdev} spread={rep.total_spread} "
              f"pass_flips={rep.pass_flips} UNSTABLE={rep.unstable}")
        print("  항목별 stdev:", rep.per_criterion_stdev)
        return 0

    ev = score_submission(provider, rubric, submission, golden)
    print(f"[채점] {rubric.rubric_id} v{rubric.version}  총점={ev.weighted_total}  "
          f"{'PASS' if ev.passed else 'FAIL'} (임계 {rubric.pass_threshold})")
    for s in ev.scores:
        print(f"  {s.criterion_id} {s.score}점 — {s.evidence}")
    print("총평:", ev.overall_comment)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
