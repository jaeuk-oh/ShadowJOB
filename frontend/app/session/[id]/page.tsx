"use client";

import { use, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Scenario, SessionView, SubmitResult, Weapons } from "@/lib/types";
import { ProgressBar } from "@/app/components/ProgressBar";
import { PersonaChat } from "@/app/components/PersonaChat";
import { AssetViewer } from "@/app/components/AssetViewer";
import { BriefEditor } from "@/app/components/BriefEditor";
import { ReviewFeedback } from "@/app/components/ReviewFeedback";
import { WeaponView } from "@/app/components/WeaponView";
import { SurveyWidget } from "@/app/components/SurveyWidget";

export default function Workspace({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [session, setSession] = useState<SessionView | null>(null);
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [weapons, setWeapons] = useState<Weapons | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const s = await api.getSession(id);
        setSession(s);
        setScenario(await api.getScenario(s.scenario_id));
      } catch (e) {
        setError(`세션을 불러오지 못했습니다: ${(e as ApiError).message}`);
      }
    })();
  }, [id]);

  async function handleSubmit(text: string) {
    setBusy(true);
    setError(null);
    try {
      const res = await api.submit(id, text);
      setResult(res);
      const s = await api.getSession(id);
      setSession(s);
      if (s.completed) setWeapons(await api.getWeapons(id));
    } catch (e) {
      const err = e as ApiError;
      setError(
        err.status === 503
          ? "LLM 키가 없어 채점할 수 없습니다 (백엔드 OPENAI_API_KEY 설정 필요)."
          : `제출 실패: ${err.message}`
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleDecision(note: string) {
    try {
      await api.addDecision(id, note);
    } catch {
      /* 비치명적 */
    }
  }

  if (error && !scenario)
    return (
      <div className="container">
        <p className="error">{error}</p>
      </div>
    );
  if (!scenario || !session)
    return (
      <div className="container">
        <p className="muted">불러오는 중…</p>
      </div>
    );

  const completed = session.state === "completed";
  const revising = session.state === "revising";

  return (
    <div>
      <div
        style={{
          display: "flex",
          gap: 12,
          alignItems: "center",
          padding: "10px 14px",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <span className="label">📌 가상 실무 프로젝트</span>
        <ProgressBar state={session.state} />
        {error && <span className="error" style={{ marginLeft: "auto" }}>{error}</span>}
      </div>

      <div className="workspace" style={{ height: "calc(100vh - 53px)" }}>
        <PersonaChat sessionId={id} personas={scenario.personas} />
        <AssetViewer csv={scenario.assets.cs_logs_csv} dashboardMd={scenario.assets.dashboard_md} />
        <div className="col">
          <div className="col-head">산출물</div>
          <div className="col-body">
            <BriefEditor
              template={scenario.brief_template}
              onSubmit={handleSubmit}
              onAddDecision={handleDecision}
              busy={busy}
              disabled={completed}
              revising={revising}
            />
            {result && <ReviewFeedback result={result} />}
            {completed && weapons && <WeaponView weapons={weapons} />}
            {completed && !weapons && (
              <p className="muted" style={{ marginTop: 12 }}>무기 패키지를 불러오는 중…</p>
            )}
            {completed && <SurveyWidget sessionId={id} />}
          </div>
        </div>
      </div>
    </div>
  );
}
