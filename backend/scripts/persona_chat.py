"""P0-2 수동 페르소나 대화 REPL. (OPENAI_API_KEY 필요)

사용:
  python scripts/persona_chat.py            # 기본 시나리오 saver-studio
  /who                                       # 등장인물 목록
  /to <persona_id>                           # 대화 상대 전환
  (그 외 입력)                                # 현재 상대에게 메시지
  /quit
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.llm.provider import build_default_provider  # noqa: E402
from app.personas.orchestrator import SessionPersonas  # noqa: E402

SCENARIO = "saver-studio"


def main() -> int:
    settings = get_settings()
    if not settings.has_openai:
        print("OPENAI_API_KEY가 없습니다. .env 설정 후 실행하세요.", file=sys.stderr)
        return 2

    provider = build_default_provider(settings)
    session = SessionPersonas.create(SCENARIO, provider)
    ids = session.persona_ids()
    current = ids[0]
    print(f"[{SCENARIO}] 등장인물: {', '.join(ids)}")
    print(f"현재 상대: {current}  (/to 로 전환, /who 목록, /quit 종료)")

    while True:
        try:
            line = input(f"{current} > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            continue
        if line == "/quit":
            return 0
        if line == "/who":
            print("  " + ", ".join(ids))
            continue
        if line.startswith("/to "):
            target = line[4:].strip()
            if target in session.agents:
                current = target
            else:
                print(f"  없는 인물: {target}")
            continue
        reply = session.send(current, line)
        print(f"  {current}: {reply}")


if __name__ == "__main__":
    raise SystemExit(main())
