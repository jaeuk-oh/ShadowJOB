"use client";

import { useState } from "react";

export function BriefEditor({
  template,
  onSubmit,
  onAddDecision,
  busy,
  disabled,
  revising,
}: {
  template: string;
  onSubmit: (text: string) => void;
  onAddDecision: (note: string) => Promise<void>;
  busy: boolean;
  disabled: boolean;
  revising: boolean;
}) {
  const [text, setText] = useState("");
  const [decision, setDecision] = useState("");
  const [savedDecisions, setSavedDecisions] = useState<string[]>([]);

  function useTemplate() {
    if (!text) setText(template);
  }

  async function saveDecision() {
    const n = decision.trim();
    if (!n) return;
    await onAddDecision(n);
    setSavedDecisions((d) => [...d, n]);
    setDecision("");
  }

  return (
    <div className="card">
      <h4 style={{ marginTop: 0 }}>
        Problem Brief {revising ? "(재작업)" : ""}
      </h4>
      {!disabled && (
        <button className="secondary" onClick={useTemplate} style={{ marginBottom: 8 }}>
          템플릿 불러오기
        </button>
      )}
      <textarea
        rows={14}
        value={text}
        disabled={disabled}
        placeholder="여기에 직접 작성하세요. 모든 진단에 로그/지표 근거를 붙이세요."
        onChange={(e) => setText(e.target.value)}
      />
      <p className="hint">
        막히면 동료에게 묻고 자료를 다시 보세요. 정보가 엇갈리는 건 정상입니다 — 데이터로 판단하세요.
      </p>

      <div style={{ marginTop: 10 }}>
        <b>의사결정 로그</b>{" "}
        <span className="hint">왜 그렇게 판단했는지 — 검증용 무기가 됩니다</span>
        <div className="chat-input">
          <input
            value={decision}
            placeholder="예: 환불 미해결인데 응답이 빨라 인프라 아닌 KB 문제로 판단"
            onChange={(e) => setDecision(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && saveDecision()}
          />
          <button className="secondary" onClick={saveDecision}>
            기록
          </button>
        </div>
        {savedDecisions.length > 0 && (
          <ul className="hint">
            {savedDecisions.map((d, i) => (
              <li key={i}>{d}</li>
            ))}
          </ul>
        )}
      </div>

      {!disabled && (
        <button
          style={{ marginTop: 12 }}
          disabled={busy || !text.trim()}
          onClick={() => onSubmit(text)}
        >
          {busy ? "제출/채점 중…" : revising ? "재제출" : "제출"}
        </button>
      )}
    </div>
  );
}
