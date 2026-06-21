# FIELD — AX PM 단일 직무 MVP

> 실제처럼 굴러가는 **가상 회사** 안에서 실무 과제를 수행하게 하여, 취준생이 취업 전선에서 바로 쓸 수 있는
> **합격 무기 3종**(서류 산출물 · 면접 STAR 서사 · 검증용 과정 기록)을 **한 번의 경험에서 동시에** 얻게 하는 서비스.

- **단일 직무 MVP:** AX (AI Transformation) Product Manager
- **시나리오:** 고객사 AI CS봇 갱신 위기 (세이버스튜디오 케이스)
- **스택:** FastAPI(Python) · Next.js · Supabase · OpenAI API

---

## 1. 왜 만들었는가 (Why)

**경험의 악순환.** 채용은 경력을 요구하고, 경력은 채용을 요구한다. 신입은 이 닫힌 고리 밖에 선다.
"말할 실무 경험이 없어서" 면접에서 막히는 사람이 핵심 타깃이다.

**기존 해법의 한계**
- **Forage(가상 직무 시뮬):** 인정이 *기업 파트너십*에 묶여 솔로가 복제 불가, 정적 녹화 콘텐츠. "경력란에 적지 말라"고 명시.
- **부트캠프:** 수강생 결과물이 전원 동일 → 변별력 소멸.
- **AI 면접/자소서 도구:** 남는 산출물이 없다. 통과 기술일 뿐 역량 증거가 아니다.

**우리가 다르게 푸는 지점**
1. **진짜 산출물** — 보증(기업 인정) 대신 결과물 자체가 증거. 맥락은 시뮬이어도 결과물은 진짜라, 제3자 보증이 필요 없다.
2. **AI 네이티브 적응형** — 정적 녹화가 아니라, 사용자 답변·수준에 반응하는 살아있는 회사.
3. **합격 무기 3종 동시 생산** — 서류용 산출물에 그치지 않고 면접용 서사, 검증용 과정 기록까지 한 번에. (← 핵심 차별점)

**북극성 지표:** 사용 시간·리얼리즘이 아니라 **"실제 취업 성공 확률을 높였는가."**
리얼리즘은 무기를 뽑기 위한 수단일 뿐, 목표가 아니다.

---

## 2. 핵심 개념

| 용어 | 뜻 |
|---|---|
| **합격 무기 3종** | ① 증거형(서류 산출물) · ② 서사형(면접 STAR+예상질문) · ③ 신뢰형(의사결정 로그+반려 후 수정 이력) |
| **반려 루프** | 1차 산출물을 까고 재작업시키는 과정. "처음에 못 맞추고 피드백 받아 고친 과정"이 면접 최강 성장 서사 → 무기 제조 공정 |
| **선택적 리얼리즘** | 신호를 만드는 차원(모호성·반려·진짜 자료·진짜 채점)만 리얼하게. 비용만 드는 차원(4주 대기·주40시간 모사·행정 잡무)은 압축/생략 |
| **골든셋·루브릭** | 채점 기준이 되는 모범답안·평가 세트. **채점이 무너지면 산출물 신뢰가 무너진다 → 제품의 해자** |
| **역량모델** | "직무특화 + 일반 채용 요구역량"을 항목화한 것. **시나리오 과제와 평가 루브릭을 동시에 구동하는 단일 출처** |

핵심 가설(반드시 참이어야 함): **H1** AI 시뮬 산출물(+과정 기록)이 그 자체로 채용 신호가 된다 · **H3** 평가 엔진 채점이 신뢰할 만큼 일관적이다.

---

## 3. 아키텍처와 설계 의도 (왜 이렇게 설계했는가)

```
[프론트엔드 Next.js]  슬랙/메일 모사 · 자료 뷰어 · 산출물 에디터 · 무기 뷰 · 계측 대시보드
        │ REST
[백엔드 FastAPI]
   ├─ scenario/      시나리오 로더 — 비노출(정답 키) 섹션 제거 후 자료 노출
   ├─ personas/      페르소나 3인 오케스트레이터(매니저/고객/엔지니어) + 매니저 반려 피드백
   ├─ evaluation/    ★평가 엔진 — 루브릭 채점 + 채점 일관성 하니스(H3)
   ├─ session/       1회전 상태 기계 + 세션 레코드(무기 3종 재료 보관)
   ├─ weapons/       무기 3종 생성기
   ├─ metrics/       베타 계측 집계(완주율·STAR·블라인드·퍼널)
   ├─ llm/           LLMProvider 추상화 (OpenAI / Mock)
   ├─ repository/    SessionRepository 추상화 (인메모리 / Supabase)
   └─ services/      배선 계층(유스케이스)
[데이터·자산: 파일 기반, 버전 관리]
   competency-model/ · scenarios/ · golden-sets/
```

설계 결정과 그 이유:

1. **역량모델을 시나리오·루브릭의 "단일 출처"로 둔다.**
   채점 기준이 *실제 채용에서 요구되는 역량*에 정박해야 무기의 신뢰(H1·H3)가 성립한다. 그래서 역량 리서치 →
   역량모델 → (시나리오 과제 + 루브릭)이 같은 출처에서 파생되도록 했다. (`competency-model/ax-pm.md`)

2. **평가 엔진을 "해자"로 보고 가장 먼저 de-risk했다.**
   제품 실패의 가장 큰 리스크는 "채점이 후하거나 들쭉날쭉"(R2/H3)이다. 그래서 실무 빌드 순서를
   **평가 엔진부터** 잡고, **동일 산출물 반복 채점 편차 측정 하니스**(`evaluation/consistency.py`)를 회귀 테스트로 두었다.

3. **외부 의존성(LLM·DB)을 인터페이스 뒤로 추상화했다.**
   - `LLMProvider`(`llm/provider.py`): 실서비스는 `OpenAIProvider`, 테스트는 `MockProvider`.
   - `SessionRepository`(`repository/`): 기본 인메모리, 키가 있으면 Supabase.
   덕분에 **OpenAI 키 없이도 전 로직을 결정적으로 테스트**할 수 있다(실제로 35개 테스트가 키 없이 통과). LLM 콜은
   비결정적·유료라 테스트 스위트에 넣지 않는다는 실무 원칙을 따른 것.

4. **데이터/평가 작업이 핵심이라 백엔드를 Python으로.**
   루브릭 채점, CSV 진단, 일관성 하니스는 Python 생태계와 정합. pydantic으로 구조화 출력을 검증한다.

5. **무기 ③(과정 기록)을 위해 모든 LLM 산출을 원본 입력과 함께 저장한다.**
   "AI로 만든 거 아니냐"는 의심에 대한 방어선은 *결과물*이 아니라 *사고 과정*이다. 의사결정 로그·반려/수정 이력을
   세션에 적재해 재현·감사 가능하게 했다.

6. **정직한 포지셔닝을 코드에 박았다.**
   산출물에 "가상 실무 프로젝트" 라벨을 강제(`weapons/generator.py`의 `PROJECT_LABEL`). *경력인 척*하면 검증 단계에서 부러진다.

---

## 4. 기술 선택 이유 (왜 이 라이브러리인가)

| 선택 | 이유 |
|---|---|
| **FastAPI (Python)** | 평가/채점·CSV·데이터 작업이 핵심. pydantic으로 요청/구조화 출력 검증. 타입드 라우팅 + 자동 문서 |
| **OpenAI Structured Outputs (JSON Schema)** | 채점 결과의 **형태를 강제**(항목별 정수 점수+근거) → 파싱 견고성·채점 일관성(H3). 낮은 temperature와 결합 |
| **Supabase** | 관리형 Postgres + Auth(매직링크) + Storage를 한 번에. PoC 인프라·인증 부담 최소화. supabase 패키지는 지연 임포트라 키 없으면 인메모리로 폴백 |
| **Next.js (App Router) + TypeScript** | 슬랙/메일 모사 UI·자료 뷰어를 빠르게. 타입으로 API 계약 공유(`frontend/lib/types.ts`) |
| **plain CSS (Tailwind 미사용)** | PoC 의존성·빌드 표면 최소화 → 빌드 실패 위험↓. 마크다운 렌더 라이브러리 대신 자체 CSV 파서/`pre` |
| **pytest + MockProvider/InMemoryRepository** | 외부 키·네트워크 없이 결정적 검증. 직렬화 라운드트립으로 Supabase 데이터 계약까지 동시 검증 |

> 트레이드오프: 단일 Next.js 풀스택 대비 "Python+TS 2언어/2배포"로 운영 표면이 늘지만, 평가 로직의 Python 이점과
> Supabase의 인프라 절감이 이를 상쇄한다고 판단.

---

## 5. 디렉터리 구조

```
competency-model/ax-pm.md        역량모델(직무특화+일반) — 시나리오·루브릭의 출처
scenarios/saver-studio/          과제 정의 · 페르소나 3인 카드 · CS로그 CSV · 대시보드 · Brief 템플릿
golden-sets/ax-pm/               rubric.json(루브릭) · golden-01-strong.md(모범답안) · example-weak-draft.md
backend/
  app/llm/                       LLM 추상화 (OpenAI / Mock)
  app/evaluation/                루브릭 엔진 · 채점기 · 일관성 하니스
  app/personas/                  페르소나 로더·에이전트·오케스트레이터·반려 피드백
  app/session/                   상태 기계 · 세션 레코드(직렬화·계측)
  app/weapons/                   무기 3종 생성기
  app/scenario/                  시나리오 로더(비노출 strip)
  app/repository/                저장소 추상화 (인메모리 / Supabase / factory)
  app/metrics/                   베타 계측 집계
  app/services/                  배선(유스케이스)
  app/api/routes.py              FastAPI 라우트
  app/main.py                    FastAPI 엔트리
  scripts/                       run_cycle.py(P0-4) · score_brief.py · persona_chat.py
  tests/                         35개(키 불필요)
frontend/
  app/                           page(시작) · session/[id](워크스페이스) · metrics(대시보드)
  app/components/                PersonaChat · AssetViewer · BriefEditor · ReviewFeedback · WeaponView · SurveyWidget · ProgressBar
  lib/                           api.ts(클라이언트) · types.ts(계약)
```

---

## 6. 실행 방법

### 백엔드
```bash
cd backend
python -m pip install -r requirements.txt
cp .env.example .env            # OPENAI_API_KEY (선택), SUPABASE_* (선택) 입력
uvicorn app.main:app --reload   # http://localhost:8000
```

### 프론트엔드
```bash
cd frontend
npm install
cp .env.example .env.local      # NEXT_PUBLIC_API_BASE=http://localhost:8000
npm run dev                     # http://localhost:3000
```

- **키가 없어도** 시작·자료 뷰어·세션 생성·계측 대시보드는 동작한다. LLM 화면(대화·제출·무기)만 503 안내가 뜬다.
- **키가 있으면** `http://localhost:3000`에서 1회전 전체(입사 → 대화·자료분석 → Brief 제출 → 반려 → 재작업 → 완료 → 무기 3종)가 돌아간다.

### CLI (도그푸딩/검증)
```bash
cd backend
python scripts/run_cycle.py                  # 전체 1회전 → 무기 3종 실추출 (P0-4 게이트)
python scripts/score_brief.py <파일> --consistency 5   # 채점 + 편차 측정 (H3)
python scripts/persona_chat.py               # 페르소나 수동 대화 (P0-2)
```

---

## 7. 테스트 · 검증

```bash
cd backend && python -m pytest        # 35개 통과 (OpenAI 키 불필요)
cd frontend && npm run build          # 타입체크 + 프로덕션 빌드
```

- **채점 일관성(H3):** `evaluation/consistency.py` 하니스가 동일 산출물 반복 채점 편차를 측정, 임계 초과 시 `unstable` 플래그.
- **외부 의존 없는 결정적 검증:** `MockProvider` + `InMemorySessionRepository`. 인메모리 저장도 직렬화 라운드트립을 거쳐 Supabase 데이터 계약을 함께 검증.

---

## 8. 베타 계측 (북극성 검증 / `/metrics`)

PRD 성공 기준을 실제로 측정한다(합격선은 가설값 — 측정 후 확정):

| 지표 | 합격선(가설) | 수집 방법 |
|---|---|---|
| 완주율 | ≥ 50% | 세션 상태 전이 이벤트 |
| 면접 무기(STAR 자가응답) | ≥ 70% | 종료 화면 설문 위젯 |
| 산출물 품질(블라인드) | ≥ 60% | 담당자 블라인드 평가 입력 |
| 채점 일관성 | 편차 낮음 | 일관성 하니스 |

`GET /api/metrics` → 완주율·통과율·STAR·블라인드·**단계별 퍼널**. 프론트 `/metrics`에서 목표 대비 달성/미달로 표시.

---

## 9. 현황 · 로드맵

**완료**
- P0: 역량모델 · 시나리오 자산 · 루브릭/골든셋
- P1: 평가 엔진(+일관성 하니스) · 페르소나 오케스트레이터 · 상태엔진 · 세션 · 무기 생성기 · 배선(FastAPI REST) · 프론트엔드 · 베타 계측

**남은 것**
- 라이브 검증(OpenAI 키 → `run_cycle.py`로 P0-4 게이트 + H3 편차 측정)
- Supabase 라이브 영속화 검증(코드·계약 준비됨, 키만)
- P1-22 매직링크 인증·세션 재개 · P1-24 5~10명 베타 실행

**오픈 퀘스천 — 가정한 기본값(업데이트 친화 설계)**

| 항목 | 기본값 | 교체 지점 |
|---|---|---|
| 합격 산출물 표준 | Problem Brief 1종 | 산출물 타입 레지스트리(템플릿+루브릭 한 세트) |
| 반려 횟수 | 1회 고정 | `max_revisions` 설정값(점수 임계 가변 모드 플래그) |
| 골든셋 확보 | 창업자 기준 1~3개 | `golden-sets/` 파일·버전 태깅 |
| 진짜 자료 | 합성 데이터 | `scenarios/<id>/` 자산 교체 |

---

## 10. 비범위 (MVP 제외)
복수 직무·시나리오, 실시간 다일 진행, 복잡한 관계(rapport) 시뮬, 기업 파트너십/브랜드 연동, 결제·구독·기관 관리자 대시보드, 모바일 네이티브 앱.
