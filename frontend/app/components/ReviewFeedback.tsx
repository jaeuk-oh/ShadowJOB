import type { SubmitResult } from "@/lib/types";

export function ReviewFeedback({ result }: { result: SubmitResult }) {
  const ev = result.evaluation;
  return (
    <div className="card" style={{ marginTop: 12 }}>
      <h4 style={{ marginTop: 0 }}>
        채점 결과{" "}
        <span className={`pill ${ev.passed ? "pass" : "fail"}`}>
          {ev.passed ? "통과" : "반려"} · 총점 {ev.weighted_total}
        </span>
      </h4>
      {result.rejection && (
        <div className="card" style={{ background: "var(--panel-2)", marginBottom: 10 }}>
          <b>매니저 김도현</b>
          <p style={{ whiteSpace: "pre-wrap", margin: "6px 0 0" }}>{result.rejection}</p>
        </div>
      )}
      <div>
        {ev.scores.map((s) => (
          <div className="scorebar" key={s.id}>
            <span className="name">
              {s.id} · {s.score}점
            </span>
            <span className="muted">{s.evidence}</span>
          </div>
        ))}
      </div>
      {ev.overall_comment && <p className="hint">{ev.overall_comment}</p>}
    </div>
  );
}
