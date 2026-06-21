"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { DiagnosisReport } from "@/lib/types";

const SCENARIO_ID = "saver-studio";

export default function DiagnosePage() {
  const router = useRouter();
  const [text, setText] = useState("");
  const [report, setReport] = useState<DiagnosisReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    if (!text.trim()) return;
    setBusy(true);
    setError(null);
    try {
      setReport(await api.diagnose(text));
    } catch (e) {
      const err = e as ApiError;
      setError(
        err.status === 503
          ? "LLM 키가 없어 진단할 수 없습니다 (백엔드 OPENAI_API_KEY)."
          : `진단 실패: ${err.message}`
      );
    } finally {
      setBusy(false);
    }
  }

  async function startSim() {
    setStarting(true);
    try {
      const s = await api.createSession(SCENARIO_ID);
      router.push(`/session/${s.session_id}`);
    } catch (e) {
      setError(`세션 생성 실패: ${(e as ApiError).message}`);
      setStarting(false);
    }
  }

  return (
    <div className="container">
      <span className="label">진단 → 개인화 → 시뮬</span>
      <h1>이력서/포폴 진단</h1>
      <p className="muted">
        기존 이력서나 포트폴리오를 붙여넣으면, AX PM 채용 관점의 <b>개선점·부족한점</b>을 짚고
        시뮬에서 무엇을 보완하면 좋을지 알려드립니다. (붙여넣은 내용은 진단에만 사용)
      </p>

      <textarea
        rows={12}
        value={text}
        placeholder="이력서 / 포트폴리오 텍스트를 붙여넣으세요"
        onChange={(e) => setText(e.target.value)}
      />
      <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
        <button onClick={run} disabled={busy || !text.trim()}>
          {busy ? "진단 중…" : "진단하기"}
        </button>
        <button className="secondary" onClick={() => router.push("/")}>
          진단 건너뛰고 바로 시작
        </button>
      </div>
      {error && <p className="error">{error}</p>}

      {report && (
        <>
          <div className="card" style={{ marginTop: 16 }}>
            <h3 style={{ marginTop: 0 }}>
              진단 결과{" "}
              <span className={`pill ${report.meets_bar ? "pass" : "fail"}`}>
                총점 {report.weighted_total} · {report.meets_bar ? "양호" : "보완 필요"}
              </span>
            </h3>
            {report.scores.map((s) => (
              <div className="scorebar" key={s.id}>
                <span className="name">
                  {s.id} · {s.score}점
                </span>
                <span className="muted">{s.evidence}</span>
              </div>
            ))}
            {report.summary && <p className="hint">{report.summary}</p>}
          </div>

          {report.recommended_focus.length > 0 && (
            <div className="card" style={{ marginTop: 12 }}>
              <h3 style={{ marginTop: 0 }}>이번 시뮬에서 이걸 강조하세요</h3>
              <ul>
                {report.recommended_focus.map((f) => (
                  <li key={f.id} style={{ marginBottom: 6 }}>
                    <b>{f.area}</b> — {f.message}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <button style={{ marginTop: 16 }} onClick={startSim} disabled={starting}>
            {starting ? "시작 중…" : "이 포커스로 시뮬 시작하기"}
          </button>
        </>
      )}
    </div>
  );
}
