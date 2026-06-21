"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Metrics } from "@/lib/types";

function pct(v: number | null): string {
  return v === null ? "—" : `${Math.round(v * 100)}%`;
}

function Stat({
  label,
  value,
  target,
  ok,
}: {
  label: string;
  value: string;
  target?: string;
  ok?: boolean | null;
}) {
  return (
    <div className="card" style={{ flex: 1, minWidth: 180 }}>
      <div className="muted">{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700 }}>
        {value}{" "}
        {ok != null && (
          <span className={`pill ${ok ? "pass" : "fail"}`}>{ok ? "달성" : "미달"}</span>
        )}
      </div>
      {target && <div className="hint">목표 {target}</div>}
    </div>
  );
}

export default function MetricsPage() {
  const [m, setM] = useState<Metrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getMetrics()
      .then(setM)
      .catch((e: ApiError) => setError(`불러오기 실패 (${e.status})`));
  }, []);

  if (error)
    return (
      <div className="container">
        <p className="error">{error}</p>
      </div>
    );
  if (!m)
    return (
      <div className="container">
        <p className="muted">불러오는 중…</p>
      </div>
    );

  const meets = (v: number | null, t: number) => (v === null ? null : v >= t);

  return (
    <div className="container" style={{ maxWidth: 920 }}>
      <h1>베타 계측 대시보드</h1>
      <p className="muted">
        북극성 검증용 지표 (PRD §3). 합격선은 가설값 — 측정 후 확정.
      </p>

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 16 }}>
        <Stat label="총 세션" value={String(m.total_sessions)} />
        <Stat
          label="완주율"
          value={pct(m.completion_rate)}
          target={pct(m.targets.completion_rate)}
          ok={meets(m.completion_rate, m.targets.completion_rate)}
        />
        <Stat
          label="STAR 자가응답"
          value={pct(m.survey.star_self_report_rate)}
          target={pct(m.targets.star_self_report_rate)}
          ok={meets(m.survey.star_self_report_rate, m.targets.star_self_report_rate)}
        />
        <Stat
          label="블라인드 '진짜 같다'"
          value={pct(m.blind_eval.looks_real_rate)}
          target={pct(m.targets.blind_looks_real_rate)}
          ok={meets(m.blind_eval.looks_real_rate, m.targets.blind_looks_real_rate)}
        />
      </div>

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 16 }}>
        <Stat label="완료" value={`${m.completed} / ${m.total_sessions}`} />
        <Stat label="통과율(완료 중)" value={pct(m.pass_rate)} />
        <Stat label="반려 후 재작업" value={String(m.revised_at_least_once)} />
        <Stat
          label="설문 응답"
          value={`${m.survey.answered}건`}
        />
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>퍼널 (도달 최대 단계)</h3>
        <table>
          <thead>
            <tr>
              <th>단계</th>
              <th>세션 수</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(m.funnel).map(([k, v]) => (
              <tr key={k}>
                <td>{k}</td>
                <td>{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
