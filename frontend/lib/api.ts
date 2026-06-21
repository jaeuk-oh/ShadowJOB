import type {
  Scenario,
  SessionView,
  SubmitResult,
  Weapons,
} from "./types";

const BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

export const api = {
  getScenario: (id: string) => req<Scenario>(`/api/scenarios/${id}`),

  createSession: (scenario_id: string, max_revisions = 1) =>
    req<SessionView>(`/api/sessions`, {
      method: "POST",
      body: JSON.stringify({ scenario_id, max_revisions }),
    }),

  getSession: (id: string) => req<SessionView>(`/api/sessions/${id}`),

  addDecision: (id: string, note: string) =>
    req<{ ok: boolean }>(`/api/sessions/${id}/decisions`, {
      method: "POST",
      body: JSON.stringify({ note }),
    }),

  chat: (id: string, persona_id: string, message: string) =>
    req<{ persona_id: string; reply: string }>(`/api/sessions/${id}/chat`, {
      method: "POST",
      body: JSON.stringify({ persona_id, message }),
    }),

  submit: (id: string, text: string) =>
    req<SubmitResult>(`/api/sessions/${id}/submit`, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),

  getWeapons: (id: string) => req<Weapons>(`/api/sessions/${id}/weapons`),
};
