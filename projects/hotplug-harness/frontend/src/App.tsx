import { FormEvent, useEffect, useState } from "react";
import { api } from "./api";
import type { DemoInfo, PluginSummary, RunRecord } from "./types";

const STATUS_LABEL: Record<string, string> = {
  running: "运行中",
  succeeded: "成功",
  cancelled: "已取消",
  circuit_open: "熔断",
  budget_exceeded: "预算耗尽",
  failed: "失败",
  policy_blocked: "策略拦截",
};

const KIND_LABEL: Record<string, string> = {
  model: "模型提议",
  tool: "工具执行",
  policy: "策略",
  circuit: "熔断",
  budget: "预算",
  cancel: "取消",
};

const DEMO_ORDER = ["happy", "circuit", "budget", "policy"] as const;

function Badge({ status }: { status: string }) {
  return (
    <span className={`badge badge-${status}`}>
      {STATUS_LABEL[status] ?? status}
      <code>{status}</code>
    </span>
  );
}

function PluginColumn({ plugins }: { plugins: PluginSummary | null }) {
  if (!plugins) {
    return <p className="muted">尚未连上后端…</p>;
  }
  const groups: { title: string; items: string[]; hint: string }[] = [
    { title: "Tools", items: plugins.tools, hint: "plugins/tools/" },
    { title: "Models", items: plugins.models, hint: "plugins/models/" },
    { title: "Policies", items: plugins.policies, hint: "plugins/policies/" },
  ];
  return (
    <>
      {groups.map((g) => (
        <div key={g.title} className="plugin-group">
          <h3>
            {g.title} <span className="hint">{g.hint}</span>
          </h3>
          <ul>
            {g.items.map((name) => (
              <li key={name}>
                <code>{name}</code>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </>
  );
}

function Timeline({ run }: { run: RunRecord | null }) {
  if (!run) {
    return <p className="muted">先发起一次 Run，或点演示按钮。时间线会显示每一步 kind。</p>;
  }
  return (
    <>
      <div className="run-meta">
        <Badge status={run.status} />
        <div className="meta-grid">
          <span>run</span>
          <code>{run.run_id.slice(0, 8)}</code>
          <span>model</span>
          <code>{run.model_name}</code>
          <span>final</span>
          <code>{run.final || "—"}</code>
          <span>steps / tools</span>
          <code>
            {run.step} / {run.tool_calls}
          </code>
          <span>隔离键</span>
          <code>
            {run.isolation.tenant_id} / {run.isolation.user_id} / {run.isolation.thread_id}
          </code>
        </div>
      </div>
      <table className="timeline">
        <thead>
          <tr>
            <th>step</th>
            <th>kind</th>
            <th>detail</th>
          </tr>
        </thead>
        <tbody>
          {run.events.map((e, i) => (
            <tr key={`${e.step}-${e.kind}-${i}`}>
              <td>{e.step}</td>
              <td>
                <span className={`kind kind-${e.kind}`}>{KIND_LABEL[e.kind] ?? e.kind}</span>
              </td>
              <td>
                <code>{JSON.stringify(e.detail)}</code>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

export default function App() {
  const [plugins, setPlugins] = useState<PluginSummary | null>(null);
  const [demos, setDemos] = useState<Record<string, DemoInfo>>({});
  const [recent, setRecent] = useState<RunRecord[]>([]);
  const [selected, setSelected] = useState<RunRecord | null>(null);
  const [error, setError] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [apiUp, setApiUp] = useState<boolean | null>(null);

  const [tenantId, setTenantId] = useState("t1");
  const [userId, setUserId] = useState("u1");
  const [threadId, setThreadId] = useState("th-manual");
  const [modelName, setModelName] = useState("scripted_happy");
  const [maxSteps, setMaxSteps] = useState(8);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await api.health();
        if (cancelled) return;
        setApiUp(true);
        const [p, d, runs] = await Promise.all([api.plugins(), api.demos(), api.runs()]);
        if (cancelled) return;
        setPlugins(p);
        setDemos(d);
        setRecent(runs);
        if (runs[0]) setSelected(runs[0]);
        if (p.models.length) setModelName((cur) => (p.models.includes(cur) ? cur : p.models[0]));
      } catch (err) {
        if (cancelled) return;
        setApiUp(false);
        setError(err instanceof Error ? err.message : String(err));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function onReload() {
    setBusy(true);
    setError("");
    try {
      const p = await api.reload();
      setPlugins(p);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  function remember(run: RunRecord) {
    setSelected(run);
    setRecent((prev) => [run, ...prev.filter((r) => r.run_id !== run.run_id)].slice(0, 20));
  }

  async function submitRun(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const run = await api.startRun({
        tenant_id: tenantId,
        user_id: userId,
        thread_id: threadId,
        model_name: modelName,
        max_steps: maxSteps,
      });
      remember(run);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function fireDemo(name: string) {
    setBusy(true);
    setError("");
    try {
      const run = await api.demo(name);
      remember(run);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <header className="header">
        <div>
          <h1>热插拔 Agent Harness 控制台</h1>
          <p className="sub">
            后端 FastAPI :8000 · 前端 Vite :5173 · 无 LLM Key · 脚本模型插件
          </p>
        </div>
        <div className="header-actions">
          <span className={`dot ${apiUp ? "ok" : apiUp === false ? "bad" : ""}`}>
            {apiUp ? "API 已连接" : apiUp === false ? "API 未连接" : "检测中"}
          </span>
          <button type="button" onClick={() => void onReload()} disabled={busy}>
            重新扫描插件
          </button>
        </div>
      </header>

      <div className="explainer">
        Model 只 propose；Harness 管 Budget / Circuit / Policy
      </div>

      {error ? <div className="error">错误：{error}</div> : null}

      <main className="grid">
        <section className="card">
          <h2>已加载插件</h2>
          <p className="hint">从磁盘 `plugins/` 热加载，不改核心循环。</p>
          <PluginColumn plugins={plugins} />
        </section>

        <section className="card">
          <h2>发起一次 Run</h2>
          <form className="form" onSubmit={(e) => void submitRun(e)}>
            <label>
              tenant_id
              <input value={tenantId} onChange={(e) => setTenantId(e.target.value)} />
            </label>
            <label>
              user_id
              <input value={userId} onChange={(e) => setUserId(e.target.value)} />
            </label>
            <label>
              thread_id
              <input value={threadId} onChange={(e) => setThreadId(e.target.value)} />
            </label>
            <label>
              model
              <select value={modelName} onChange={(e) => setModelName(e.target.value)}>
                {(plugins?.models ?? [modelName]).map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </label>
            <label>
              max_steps
              <input
                type="number"
                min={1}
                max={32}
                value={maxSteps}
                onChange={(e) => setMaxSteps(Number(e.target.value) || 8)}
              />
            </label>
            <button type="submit" disabled={busy || !apiUp}>
              开始运行
            </button>
          </form>

          <h3 className="demos-title">演示场景</h3>
          <div className="demos">
            {DEMO_ORDER.map((name) => {
              const info = demos[name];
              return (
                <button
                  key={name}
                  type="button"
                  className={`demo demo-${name}`}
                  disabled={busy || !apiUp}
                  title={info?.proves}
                  onClick={() => void fireDemo(name)}
                >
                  <strong>{info?.label ?? name}</strong>
                  <span>{info?.proves ?? name}</span>
                </button>
              );
            })}
          </div>

          <h3 className="demos-title">最近 Runs</h3>
          {recent.length === 0 ? (
            <p className="muted">还没有 run。</p>
          ) : (
            <ul className="recent">
              {recent.map((r) => (
                <li key={r.run_id}>
                  <button
                    type="button"
                    className={selected?.run_id === r.run_id ? "active" : ""}
                    onClick={() => setSelected(r)}
                  >
                    <Badge status={r.status} />
                    <code>{r.model_name}</code>
                    <span>{r.run_id.slice(0, 8)}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card">
          <h2>事件时间线</h2>
          <p className="hint">每一步由 Harness 记账：model / tool / policy / circuit / budget。</p>
          <Timeline run={selected} />
        </section>
      </main>

      <footer>
        加工具 = 往 plugins/tools/ 丢一个文件，然后点「重新扫描插件」。核心 harness.py 零 diff。
      </footer>
    </div>
  );
}
