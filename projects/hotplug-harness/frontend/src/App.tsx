import { FormEvent, useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { ChatMessage, PluginSummary, RunRecord, SampleChip } from "./types";

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

const DEFAULT_SAMPLES: SampleChip[] = [
  { id: "happy", label: "正常问答", fill: "请用一句话解释什么是 Agent Harness？" },
  { id: "circuit", label: "触发熔断", fill: "请演示死循环熔断：模型不停调用同一工具" },
  { id: "budget", label: "超预算", fill: "请演示超步数预算耗尽：每次不同工具签名一直跑" },
  { id: "policy", label: "越权工具", fill: "请尝试越权调用 forbidden 的 drop_db 工具" },
];

function Badge({ status }: { status: string }) {
  return (
    <span className={`badge badge-${status}`}>
      {STATUS_LABEL[status] ?? status}
      <code>{status}</code>
    </span>
  );
}

function Timeline({ run }: { run: RunRecord | null }) {
  if (!run) {
    return <p className="muted">发一条消息后，这里会显示本次 Run 的事件时间线。</p>;
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
          <span>route</span>
          <code>{run.route ?? "—"}</code>
          <span>steps / tools</span>
          <code>
            {run.step} / {run.tool_calls}
          </code>
          <span>隔离键</span>
          <code>
            {run.isolation.tenant_id} / {run.isolation.user_id} / {run.isolation.thread_id}
          </code>
          <span>budget</span>
          <code>
            {run.budget
              ? `steps≤${run.budget.max_steps} tools≤${run.budget.max_tool_calls}`
              : "—"}
          </code>
          <span>circuit</span>
          <code>{run.circuit_limit ?? "—"}</code>
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

function PluginStrip({ plugins }: { plugins: PluginSummary | null }) {
  if (!plugins) return <span className="muted">插件未加载</span>;
  return (
    <div className="plugin-strip">
      <span>
        Tools <code>{plugins.tools.join(", ") || "—"}</code>
      </span>
      <span>
        Models <code>{plugins.models.join(", ") || "—"}</code>
      </span>
      <span>
        Policies <code>{plugins.policies.join(", ") || "—"}</code>
      </span>
    </div>
  );
}

let msgSeq = 0;
function nextId(prefix: string) {
  msgSeq += 1;
  return `${prefix}-${msgSeq}-${Date.now()}`;
}

export default function App() {
  const [plugins, setPlugins] = useState<PluginSummary | null>(null);
  const [samples, setSamples] = useState<SampleChip[]>(DEFAULT_SAMPLES);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "system",
      text: "像真实助手一样提问。关键词会触发教学路径：死循环/熔断 → 熔断；预算/超步 → 预算；越权/forbidden → 策略拦截。旁侧面板展示 Harness 控制面。",
    },
  ]);
  const [latestRun, setLatestRun] = useState<RunRecord | null>(null);
  const [input, setInput] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [apiUp, setApiUp] = useState<boolean | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await api.health();
        if (cancelled) return;
        setApiUp(true);
        const [p, chips] = await Promise.all([api.plugins(), api.samples().catch(() => DEFAULT_SAMPLES)]);
        if (cancelled) return;
        setPlugins(p);
        if (chips?.length) setSamples(chips);
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

  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, busy]);

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

  async function sendMessage(raw: string) {
    const text = raw.trim();
    if (!text || busy) return;

    setBusy(true);
    setError("");
    setInput("");

    const userMsg: ChatMessage = { id: nextId("u"), role: "user", text };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const run = await api.chat({
        message: text,
        tenant_id: "t1",
        user_id: "u1",
        thread_id: "th-chat",
      });
      setLatestRun(run);
      const reply =
        run.reply ||
        run.final ||
        `（无回复文本，status=${run.status}）`;
      const assistantMsg: ChatMessage = {
        id: nextId("a"),
        role: "assistant",
        text: reply,
        run,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      setMessages((prev) => [
        ...prev,
        { id: nextId("e"), role: "system", text: `请求失败：${msg}` },
      ]);
    } finally {
      setBusy(false);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void sendMessage(input);
  }

  function fillChip(chip: SampleChip) {
    setInput(chip.fill);
  }

  return (
    <div className="page">
      <header className="header">
        <div>
          <h1>热插拔 Agent Harness · Q&A 控制台</h1>
          <p className="sub">
            聊天驱动 Run · 后端 FastAPI :8000 · 前端 Vite :5173 · 无 LLM Key · 脚本模型插件
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
        <span className="pill">Model propose</span>
        <span className="arrow">→</span>
        <span className="pill">Harness enforce（Budget / Circuit / Policy）</span>
      </div>

      {error ? <div className="error">错误：{error}</div> : null}

      <main className="chat-layout">
        <section className="card chat-panel">
          <h2>对话</h2>
          <p className="hint">像真实助手一样提问；场景示例只填充输入框，仍以聊天消息提交。</p>

          <div className="chips" aria-label="场景示例">
            <span className="chips-label">场景示例</span>
            {samples.map((c) => (
              <button
                key={c.id}
                type="button"
                className={`chip chip-${c.id}`}
                disabled={busy || !apiUp}
                title={c.fill}
                onClick={() => fillChip(c)}
              >
                {c.label}
              </button>
            ))}
          </div>

          <div className="messages" ref={listRef}>
            {messages.map((m) => (
              <div key={m.id} className={`bubble bubble-${m.role}`}>
                <div className="bubble-role">
                  {m.role === "user" ? "你" : m.role === "assistant" ? "助手" : "系统"}
                  {m.run ? (
                    <span className="bubble-meta">
                      <Badge status={m.run.status} />
                      <code>{m.run.model_name}</code>
                    </span>
                  ) : null}
                </div>
                <div className="bubble-text">{m.text}</div>
              </div>
            ))}
            {busy ? (
              <div className="bubble bubble-system">
                <div className="bubble-text">Harness 运行中…</div>
              </div>
            ) : null}
          </div>

          <form className="composer" onSubmit={onSubmit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="问点什么…"
              disabled={busy || !apiUp}
              aria-label="消息输入"
            />
            <button type="submit" disabled={busy || !apiUp || !input.trim()}>
              发送
            </button>
          </form>
        </section>

        <section className="card side-panel">
          <h2>本次 Run · 控制面</h2>
          <p className="hint">状态、隔离键、事件时间线、工具调用次数 —— 证明 Harness 拥有 Loop。</p>
          <Timeline run={latestRun} />
        </section>
      </main>

      <footer>
        <PluginStrip plugins={plugins} />
        <p>
          加工具 = 往 plugins/tools/ 丢一个文件，然后点「重新扫描插件」。核心 harness.py 零
          diff。旧演示按钮已改为输入芯片；也可用 <code>POST /api/demos/&#123;name&#125;</code>。
        </p>
      </footer>
    </div>
  );
}
