"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Scenario } from "@/lib/types";

const SCENARIO_ID = "saver-studio";

export default function StartPage() {
  const router = useRouter();
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    api
      .getScenario(SCENARIO_ID)
      .then(setScenario)
      .catch((e: ApiError) =>
        setError(`시나리오를 불러오지 못했습니다 (${e.status}). 백엔드가 켜져 있나요?`)
      );
  }, []);

  async function start() {
    setStarting(true);
    setError(null);
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
      <span className="label">📌 가상 실무 프로젝트 — 실제 고용 경력 아님</span>
      <h1>FIELD — AX Product Manager</h1>
      {error && <p className="error">{error}</p>}
      {!scenario && !error && <p className="muted">불러오는 중…</p>}
      {scenario && (
        <>
          <div className="card" style={{ marginBottom: 16 }}>
            <h3>입사 안내</h3>
            <p style={{ whiteSpace: "pre-wrap" }}>{scenario.background}</p>
          </div>
          <div className="card" style={{ marginBottom: 16 }}>
            <h3>첫 과제 (매니저 김도현)</h3>
            <p style={{ whiteSpace: "pre-wrap" }}>{scenario.task_message}</p>
          </div>
          <div className="card" style={{ marginBottom: 16 }}>
            <h3>함께 일할 사람들</h3>
            <ul>
              {scenario.personas.map((p) => (
                <li key={p.persona_id}>
                  <b>{p.name}</b> <span className="muted">— {p.role}</span>
                </li>
              ))}
            </ul>
          </div>
          <button onClick={start} disabled={starting}>
            {starting ? "입사 중…" : "입사하기 (세션 시작)"}
          </button>
          <p className="hint">
            첫날처럼 시작됩니다. 자료를 직접 열어보고, 동료들과 이야기하고, Problem Brief를 써서 제출하세요.
          </p>
        </>
      )}
    </div>
  );
}
