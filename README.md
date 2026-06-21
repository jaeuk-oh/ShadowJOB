# FIELD — AX PM 단일 직무 MVP

실제처럼 굴러가는 가상 회사 안에서 실무 과제를 수행하게 하여, 취준생이 취업 전선에서 쓸 수 있는
**합격 무기 3종**(서류 산출물 · 면접 STAR 서사 · 검증용 과정 기록)을 한 번의 경험에서 동시에 얻게 하는 서비스.

- 단일 직무 MVP: **AX (AI Transformation) Product Manager**
- 시나리오: 고객사 AI CS봇 갱신 위기 (세이버스튜디오 케이스)
- 스택: FastAPI(백) · Next.js(프론트) · Supabase(DB·Auth·Storage) · OpenAI API

## 개발 단계

| 단계 | 내용 |
|---|---|
| **P0** | 도그푸딩 — 역량 리서치 → 시나리오/루브릭 → 무기 3종 수동 추출 검증 |
| **P1** | 단일 직무 수직 완성 — 시뮬→평가→무기 자동화 파이프라인, 5~10명 베타 |

전체 개발계획은 별도 문서 참고. 핵심 디렉터리:

- `competency-model/` — 직무특화 + 일반 요구역량 모델 (시나리오·루브릭의 출처)
- `scenarios/` — 시나리오 자산 (과제, 페르소나, 합성 자료)
- `golden-sets/` — 골든셋 + 루브릭
- `backend/` — FastAPI (페르소나 오케스트레이터, 평가 엔진, 무기 생성기)
- `frontend/` — Next.js/React
