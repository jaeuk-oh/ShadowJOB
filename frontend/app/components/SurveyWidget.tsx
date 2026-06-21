"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export function SurveyWidget({ sessionId }: { sessionId: string }) {
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function answer(value: boolean) {
    setBusy(true);
    try {
      await api.recordSurvey(sessionId, value);
      setDone(true);
    } finally {
      setBusy(false);
    }
  }

  if (done)
    return (
      <div className="card" style={{ marginTop: 12 }}>
        <p className="muted">응답 감사합니다. 베타 개선에 반영됩니다.</p>
      </div>
    );

  return (
    <div className="card" style={{ marginTop: 12 }}>
      <b>마지막 한 가지</b>
      <p style={{ margin: "6px 0" }}>
        이 경험을 면접에서 STAR로 <b>스스로 말할 수 있겠다</b>고 느끼시나요?
      </p>
      <div style={{ display: "flex", gap: 8 }}>
        <button disabled={busy} onClick={() => answer(true)}>
          예
        </button>
        <button className="secondary" disabled={busy} onClick={() => answer(false)}>
          아니오
        </button>
      </div>
    </div>
  );
}
