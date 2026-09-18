# A1 · Runtime / Harness 最小控制面

对照 JD：Runtime State、预算、Guardrail、死循环熔断（见 `docs/curriculum.md` A1）。

## 公式

`Model + Harness = Agent`

- **Model/Executor**：只提出「下一步」（final 或 tool_calls）
- **Harness**：Loop、Policy（白名单）、Budget、重复 tool 签名熔断、Cancel、Replay 日志
- **Runtime**（本课轻量版）：`start_run` 绑定 `tenant/user/thread/run`；完整 Worker/队列在 A2/A8

## 框架已有 vs 必须自建

| 能力 | LangGraph 等框架 | 本 Harness 自建 |
|------|------------------|-----------------|
| 状态图 / 边 | 有 | 可插拔 Executor |
| 租户 / 用户 / run 键 | 通常自建 | `RunState` 强制字段 |
| 工具白名单 / ACL | 弱 | `allowlist` Policy |
| step / 墙钟 / tool 预算 | 弱 | `Budget` |
| 重复 tool 死循环熔断 | 弱 | signature 滑动窗口 |
| Replay / Trace 钩子 | 需接 OTEL | `replay()` 事件账 |

## 运行

```bash
cd 03-modules/A1-runtime
python demo.py
```

## 交付清单

- [x] `harness.py`：start_run / step / cancel / replay
- [x] 故障注入：死循环、越权工具、预算耗尽
- [x] 对照表（上文）
- [x] PASS / RUN
