import sys
from pathlib import Path

# backend/ 를 import 경로에 추가 → `import app...` 동작
sys.path.insert(0, str(Path(__file__).resolve().parent))
