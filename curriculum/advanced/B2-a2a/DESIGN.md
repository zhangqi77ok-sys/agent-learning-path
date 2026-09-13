# B2 · 最小 A2A（Agent-to-Agent）

对照 B1 调研 §1.2：MCP = 工具；A2A = Agent 委托。

## 契约（HTTP JSON，教学用）

### `POST /a2a/tasks`

请求头（下行身份，缺一不可）：

| Header | 含义 |
|--------|------|
| `X-Internal-Token` | 网关签发的内部令牌（tenant/user/roles） |
| `X-Idempotency-Key` | `tenant:thread:effect` |
| `X-Trace-Id` | 链路 |
| `X-Deadline-Ms` | Unix ms；超时后服务端取消，不再跑副作用 |

Body：`{ "task_type": "summarize_policy", "payload": {...} }`

### 行为

- 验令牌；tenant 与幂等键前缀一致。
- 同幂等键重复提交 → 返回同一 `task_id` / 结果（exactly-once 外壳）。
- 超过 deadline → `cancelled`，**不**调用下游副作用。
- 取消：`POST /a2a/tasks/{id}/cancel`（同身份）。

## 挂科现场

1. 无下行身份就委托 → 拒。
2. 无幂等键 → 拒。
3. 超时后仍执行副作用 → 挂。
4. 把 A2A 当成 MCP `call_tool` → 挂（本模块独立路径，不复用 tool registry）。

## 非目标

- 完整 Google A2A 规范实现；此处是**语义最小集**便于面试口述。
