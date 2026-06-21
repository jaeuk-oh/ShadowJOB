"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { PersonaInfo } from "@/lib/types";

type Msg = { role: "user" | "assistant"; content: string };

export function PersonaChat({
  sessionId,
  personas,
}: {
  sessionId: string;
  personas: PersonaInfo[];
}) {
  const [active, setActive] = useState(personas[0]?.persona_id ?? "");
  const [histories, setHistories] = useState<Record<string, Msg[]>>({});
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const msgs = histories[active] ?? [];

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true);
    setError(null);
    setHistories((h) => ({
      ...h,
      [active]: [...(h[active] ?? []), { role: "user", content: text }],
    }));
    setInput("");
    try {
      const res = await api.chat(sessionId, active, text);
      setHistories((h) => ({
        ...h,
        [active]: [...(h[active] ?? []), { role: "assistant", content: res.reply }],
      }));
    } catch (e) {
      const err = e as ApiError;
      setError(
        err.status === 503
          ? "LLM 키가 설정되지 않아 대화를 사용할 수 없습니다 (백엔드 OPENAI_API_KEY)."
          : `오류: ${err.message}`
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="col">
      <div className="col-head">
        대화
        <div className="tabs" style={{ marginLeft: "auto" }}>
          {personas.map((p) => (
            <span
              key={p.persona_id}
              className={`tab ${active === p.persona_id ? "active" : ""}`}
              onClick={() => setActive(p.persona_id)}
              title={p.role}
            >
              {p.name}
            </span>
          ))}
        </div>
      </div>
      <div className="col-body">
        {msgs.length === 0 && (
          <p className="muted">
            {personas.find((p) => p.persona_id === active)?.name}에게 질문해보세요.
            정보가 엇갈릴 수 있으니 데이터로 교차검증하세요.
          </p>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <div className="bubble">{m.content}</div>
          </div>
        ))}
        {busy && <p className="muted">…</p>}
        {error && <p className="error">{error}</p>}
      </div>
      <div className="col-body" style={{ flex: "none", borderTop: "1px solid var(--border)" }}>
        <div className="chat-input">
          <input
            value={input}
            placeholder="메시지 입력"
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
          />
          <button onClick={send} disabled={busy}>
            보내기
          </button>
        </div>
      </div>
    </div>
  );
}
