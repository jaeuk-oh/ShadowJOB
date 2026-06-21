"use client";

import { useState } from "react";
import type { Weapons } from "@/lib/types";

function download(name: string, content: string) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

export function WeaponView({ weapons }: { weapons: Weapons }) {
  const [tab, setTab] = useState<"doc" | "star" | "proc">("doc");
  const star = weapons.star_arsenal;

  const starText = JSON.stringify(star, null, 2);

  return (
    <div className="card" style={{ marginTop: 12 }}>
      <h3 style={{ marginTop: 0 }}>🎯 합격 무기 3종</h3>
      <div className="tabs" style={{ marginBottom: 10 }}>
        <span className={`tab ${tab === "doc" ? "active" : ""}`} onClick={() => setTab("doc")}>
          ① 서류 산출물
        </span>
        <span className={`tab ${tab === "star" ? "active" : ""}`} onClick={() => setTab("star")}>
          ② 면접 STAR
        </span>
        <span className={`tab ${tab === "proc" ? "active" : ""}`} onClick={() => setTab("proc")}>
          ③ 과정 기록
        </span>
      </div>

      {tab === "doc" && (
        <>
          <pre className="dash">{weapons.document_artifact}</pre>
          <button className="secondary" onClick={() => download("brief.md", weapons.document_artifact)}>
            다운로드
          </button>
        </>
      )}

      {tab === "star" && (
        <>
          {star.star_answers.map((a, i) => (
            <div className="card" style={{ background: "var(--panel-2)", marginBottom: 8 }} key={i}>
              <b>Q. {a.question}</b>
              <p style={{ margin: "6px 0 0" }}>
                <b>S</b> {a.situation}
                <br />
                <b>T</b> {a.task}
                <br />
                <b>A</b> {a.action}
                <br />
                <b>R</b> {a.result}
              </p>
            </div>
          ))}
          <h4>예상 질문 탄약고</h4>
          <ul>
            {star.anticipated_questions.map((q, i) => (
              <li key={i}>
                <b>{q.question}</b> <span className="muted">→ {q.suggested_angle}</span>
              </li>
            ))}
          </ul>
          <button className="secondary" onClick={() => download("interview-star.json", starText)}>
            다운로드
          </button>
        </>
      )}

      {tab === "proc" && (
        <>
          <pre className="dash">{weapons.process_record}</pre>
          <button className="secondary" onClick={() => download("process-record.md", weapons.process_record)}>
            다운로드
          </button>
        </>
      )}
    </div>
  );
}
