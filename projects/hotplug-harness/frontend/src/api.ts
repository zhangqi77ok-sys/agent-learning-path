import type { DemoInfo, PluginSummary, RunRecord } from "./types";

const BASE = import.meta.env.VITE_API_BASE ?? "";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

export const api = {
  health: () => req<{ ok: boolean; plugins: PluginSummary }>("/api/health"),
  plugins: () => req<PluginSummary>("/api/plugins"),
  reload: () => req<PluginSummary & { reloaded: boolean }>("/api/plugins/reload", { method: "POST" }),
  models: () => req<string[]>("/api/models"),
  tools: () => req<string[]>("/api/tools"),
  demos: () => req<Record<string, DemoInfo>>("/api/demos"),
  runs: () => req<RunRecord[]>("/api/runs"),
  run: (id: string) => req<RunRecord>(`/api/runs/${id}`),
  startRun: (body: {
    tenant_id: string;
    user_id: string;
    thread_id: string;
    model_name: string;
    max_steps?: number;
  }) =>
    req<RunRecord>("/api/runs", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  cancel: (id: string) => req<RunRecord>(`/api/runs/${id}/cancel`, { method: "POST" }),
  demo: (name: string) => req<RunRecord>(`/api/demos/${name}`, { method: "POST" }),
};
