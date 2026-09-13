# B1 调研稿 · Durable Runtime（挂科现场版）

> 前置：A1–A9 自研控制面已合入。B 线目标：对照最新生产栈（Temporal × LangGraph/Agents SDK、MCP/A2A、上下文工程、OTEL/Langfuse），把「会说框架名」升级成「能讲清归属与失败」。
>
> 审稿人：@Agent工程师（深挖四条）· @Java高级架构师（网关/MQ/Worker 归属）
> 状态：调研稿，**未动代码**。

---

## 0. 一句话立场

- **LangGraph / Agents SDK** = 定义 Agent「下一步做什么」（脑）
- **Temporal（或等价 Durable Runtime）** = 保证「跑到一半死了还能接着跑」（肌）
- **Spring 网关 + MQ** = 身份、抬权、业务事务、命令契约（骨）
- **MCP** = 工具/资源协议；**A2A** = Agent 间委托协议 — **绝不能混成一个 SDK 调用**

面试官一听「我们上了 Temporal」就追问下面挂科现场；答不上 = 挂。

---

## 1. 深挖四条 × 挂科现场

### 1.1 Durable Execution：checkpoint 数据 ≠ 运行时续跑

| 概念 | 是什么 | 不是什么 |
|------|--------|----------|
| Checkpoint / 状态快照 | 图状态、消息、中间变量的**数据**持久化 | 不保证外部世界（HTTP 已成功）与进程崩溃后的**调度续跑** |
| Durable Execution | Workflow 历史可回放；Activity 按策略重试；换 Worker 接着跑 | 不是「把 state 塞进 Redis 就算了」 |

**挂科现场 A**：只说「LangGraph Checkpointer 能恢复」→ 被追问「tool 已打款、checkpoint 没写上，重启后呢？」答不出 ledger/idempotency。  
**及格答法**：数据恢复用 checkpoint；副作用真相在 **effect ledger + 幂等键**（我们 A2）；Temporal Activity 重试必须同一 `idempotency_key`，否则 exactly-once 是幻觉。

**挂科现场 B**：把 Temporal Workflow 当成业务事务（见 §2）。  
**及格答法**：Workflow 编排；**钱/库存事务在 Java 领域服务**；Agent 侧只发命令、收事件。

**挂科现场 C**：分不清 Workflow / Activity / Signal。

| 构件 | 扛什么 | 崩溃后谁保证 |
|------|--------|--------------|
| Workflow | 编排、分支、等待、状态机 | 事件历史回放；确定性代码 |
| Activity | 有副作用的 I/O（模型调用、工具、打外部 API） | 按 RetryPolicy 重试；**调用方必须幂等** |
| Signal / Update | HITL 批准、取消、外部事件注入 | 信号入历史；批准后仍要走 Outbox，不能 Signal 里直接打款 |

对照我们已有：A2 `effect_ledger`+`outbox` ≈ Activity 幂等外壳；A8 Worker lease ≈ Task Queue + 单 run 互斥；A3 审批 ≈ Signal，但必须带过期/快照哈希。

**B1 代码目标（审过后再做）**：最小 Temporal Worker 跑一个「审批后创建工单」Workflow；Activity 调 mock；kill Worker 后续跑；重复 Signal 不双写。

---

### 1.2 MCP vs A2A：工具调用 ≠ Agent 委托

| | MCP | A2A |
|--|-----|-----|
| 对端 | Tool / Resource Server | 另一个 Agent（可能别团队/别框架） |
| 契约 | schema、权限、沙箱 | 任务、状态、流式更新、取消 |
| 身份 | 调用方租户/用户下行到工具 ACL | **必须**下行身份 + 委托范围 |
| 幂等 | 工具级 idempotency | **任务级**幂等键（委托方 thread/run/effect） |
| 超时取消 | 工具 deadline | 委托取消必须传播，防孤儿任务 |

**挂科现场**：用 MCP `call_tool` 去「叫另一个报销 Agent」→ 对方状态、HITL、取消全丢。  
**及格答法**：工具走 MCP（我们 A5 registry+指纹+沙箱）；跨 Agent 走 A2A，payload 带 `tenant/user/trace`、`idempotency_key`、`deadline`；取消发 cancel，对端停 Activity。

**B1/B2 代码目标**：B1 只写清边界；B2 再做最小 A2A stub（HTTP）+ 身份下行负例测试。

---

### 1.3 上下文工程：进 Harness，别只堆 Prompt

**挂科现场**：上下文爆了就「总结一下塞回去」→ 丢工具结果里的租户 ACL / 引用 id，下轮越权或胡编。

**及格答法（进 Harness 策略，对齐 A1）**：

1. **Token / 步数预算**：超限先 compaction，再拒绝新 tool（A1 budget）。
2. **Tool result 预算**：大结果落对象存储，Prompt 只留摘要 + 句柄；句柄带租户。
3. **Compaction 保留硬字段**：`tenant_id`、引用 doc 版本、`approval_id`、未完成 effect 键 — 不可被摘要掉。
4. **敏感内容**：高敏 span 不进可被模型改写的 state（对齐 A3/A7 sensitivity 路由）。

**B1 交付物**：一张「compaction 保留字段清单」+ 一条负例（摘要掉 `doc_version` 导致历史 replay 错版）。

---

### 1.4 可观测：Langfuse/OTEL ↔ A6 四层门禁

| 层 | 看什么 | OTEL/Langfuse | A6 门禁 |
|----|--------|---------------|---------|
| Model | 拒答、幻觉 | generation span | Model soft + 拒答硬规则 |
| Framework | 错边、漏 tool | graph/node span | expect_tools |
| Harness | 预算、熔断、策略 | harness events | cost / circuit |
| Application | 越权、缺 cite、缺 filter | retrieve.filter 属性 | 跨租户=0；incomplete fixture 禁入 holdout |

**挂科现场**：有漂亮 Trace，发版只看「线下 +3%」。  
**及格答法**：硬门禁一票否决（A6）；坏例 `trace_to_fixture` 脱敏进 regression，下轮 CI 必跑（A9-e）。

**B1 交付物**：一张 span 命名规范（`tool.*` / `harness.*` / `workflow.*`）与 A6 字段对照表。

---

## 2. 归属表：网关鉴权 / MQ 命令 / Temporal Worker

> @Java高级架构师 审稿主表。违反 = 挂科。

| 职责 | Spring 网关 | MQ（命令/事件） | Temporal Worker（Agent Runtime） | 禁止 |
|------|-------------|-----------------|----------------------------------|------|
| 用户登录 / 抬权 | ✅ 签发短时内部令牌 | — | ❌ 不验用户密码 | Agent 直收用户 JWT 当权威 |
| 租户/角色权威 | ✅ claims 写入令牌 | 命令头复制 `tenant/user/trace` | ✅ 只信内部令牌 + 命令头 | 模型改写 tenant |
| 业务事务（下单/打款） | ✅ 领域服务本地事务 | 发「已受理」事件 | ❌ | Workflow 里直接 `UPDATE` 业务库 |
| 长任务编排 | 可选：起 Workflow | 投递 `StartRun` / `CancelRun` | ✅ Workflow+Activity | API 线程池同步死等 |
| HITL 批准 | 审批 UI / 权限 | `ApprovalGranted` 命令 | Signal 接入后 **Outbox→业务 API** | Signal 回调里直接打款 |
| 工具调用 | 策略/审计可旁路 | — | Activity + MCP | Worker 持有万能 DB 账号 |
| A2A 出站委托 | 签发下行身份 | 可选 | Activity 调对端 | 无幂等键的裸 HTTP |
| 幂等 | 业务幂等键规范 | 命令 id 去重 | Activity 幂等 + ledger | 「Temporal 会重试所以不用幂等」 |
| 观测 | access log | 消息 lag | Workflow 历史 + OTEL | 只有 LLM 文本日志 |

### Java 挂科现场（必写进口述）

1. **Temporal Workflow 当业务事务** → 回放/重试导致重复扣款或长事务锁。  
2. **Signal 批准后无 Outbox 直接打款** → Worker 崩溃或重复 Signal = 双付。正确：Signal → 记 ledger → Outbox → Java 领域 API（幂等）。

---

## 3. 与 A1–A9 的映射（面试证据）

| B1 论点 | 仓库证据 |
|---------|----------|
| checkpoint ≠ 副作用 | A2 ledger/outbox；A9-b |
| 身份下行 | A3/A9 token；四键 |
| MCP 非安全边界 | A5 指纹/沙箱 |
| 硬门禁 | A6/A9-e |
| 队列与隔离 | A8 lease/pools |
| 成本与 429 | A7 |

B1 不是推翻 A 线，是把 A2/A8 的「自研近似」对照到 Temporal 语义，并钉死 Java 边界。

---

## 4. 建议实现切片（审过后）

1. **B1-code**：Temporal Hello Durable — `CreateTicketWorkflow`；Activity 调 mock；kill -9 Worker；重复 Signal；**无**业务库事务。  
2. **文档**：本文归属表进 `curriculum/advanced/B1-durable-runtime/`。  
3. **B2**：A2A 最小委托 + 身份/幂等/取消负例。  
4. **B3**：Harness compaction 保留字段 + 负例。

---

## 5. 请审稿 checklist

- [ ] @Agent工程师：四条挂科现场是否够「打回用了 Temporal」  
- [ ] @Java高级架构师：§2 归属表是否可签字；两项 Java 挂科是否要加第三条  
- [ ] maxzq：是否批准进仓库 `docs/b1-durable-runtime-research.md` 后再开 B1-code  

