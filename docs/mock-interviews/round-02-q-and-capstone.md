# Mock Interview Round 2 · 2026-09-13

## 元信息

| 项 | 内容 |
|----|------|
| 候选人 | agent学生 |
| 深挖面试官 | Agent工程师（Q1/Q2/Q12） |
| 架构面试官 | Java高级架构师（Capstone 身份/Outbox 口径） |
| 形式 | 书面模拟，全文入库 |
| 证据库 | https://github.com/zhangqi77ok-sys/agent-learning-path |
| 前置 | Mock R1 已通过（含 O10 附录 A/B） |

## 议程与题单

| # | 题 | 侧 | 口径 |
|---|----|----|------|
| 1 | Q1 Runtime / Harness / Model | 深挖 | 10 min |
| 2 | Q2 四隔离键 | 深挖 | 8 min |
| 3 | Q12 四层 Eval | 深挖 | 10 min |
| 4 | Capstone (a) 四键演示 | 架构+深挖 | 5 min |
| 5 | Capstone (b) 幂等副作用+Outbox | 架构 | 8 min |
| 6 | Capstone (c)(d)(e) 串讲 | 深挖 | 10 min |
| — | 自由追问 | 双方 | 余量 |

---

## 逐题记录

### 题 1 · Q1：Model / Harness / Runtime

#### 面试官提问（Agent工程师）

> JD 常见口径 `Model + Harness = Agent`。请画三层：Model / Harness / Runtime。断点续跑、compaction、预算、策略、沙箱、Replay 各落哪？LangGraph 属于哪一层、缺什么？

#### 候选人解答

**分层（口述用）**

```
Model      —— 只出「下一步」（文本 / tool call）
Harness    —— Loop、状态机、compaction、预算、Guardrail、Replay、Session 生命周期
Runtime    —— 领取任务、隔离、队列/租约、配额、与 K8s/Worker/Temporal 对接
```

| 能力 | 落点 |
|------|------|
| 断点续跑（编排） | Runtime（Temporal Workflow 历史 / Worker 租约）；状态数据可在 Harness checkpoint |
| compaction | Harness（硬字段保留，见 B 线规划） |
| 预算 / 熔断 | Harness（A1 max_steps / 重复签名 circuit） |
| 策略 / 工具白名单 | Harness + 工具网关（A5） |
| 沙箱 | Harness/工具层（A5） |
| Replay | Harness 事件日志；Eval 用 Trace→fixture（A6） |

**LangGraph**：偏 **Framework/执行图**（可被 Harness 包住的执行器），**不是** Runtime，也**不提供**多租户控制面。  
挂科句：「Runtime 就是 LangGraph」「Harness 就是 Prompt」。

**证据**：`curriculum/advanced/A1-runtime/` · B1 OWNERSHIP（编排 vs 领域）

#### 追问

> checkpoint 数据续上了，算不算 Durable Execution？

#### 再答

不算完整。checkpoint 恢复的是**状态数据**；Durable Execution 还要保证**调度续跑**与 Activity 重试策略。副作用仍靠幂等键（R1/O1、B1）。两套要分开讲。

---

### 题 2 · Q2：tenant / user / thread / run

#### 面试官提问（Agent工程师）

> 解释四键。checkpoint、HITL、审计各绑谁？模型在工具参数里伪造 `tenant_id`，哪层必须拒？

#### 候选人解答

| 键 | 含义 | 典型绑定 |
|----|------|----------|
| `tenant_id` | 租户边界 | 检索 ACL、ledger、缓存键、A2A 幂等前缀 |
| `user_id` | 账号 / RBAC | 审批人、审计「谁」 |
| `thread_id` | 会话/工单，跨 run | checkpoint 主键之一、effect 键 |
| `run_id` | 一次执行尝试 | 取消、重试、单次 Trace |

- Checkpoint：至少 `(tenant_id, thread_id)`，run 挂执行史；跨租户读同 thread/run → **0 行**（Capstone a）。
- HITL：审批绑 `user`/`approver` + 快照哈希 + 过期；resume 不能只靠 `approved: true`。
- 审计：四键 + 摘要，不可被模型改写。

**伪造 tenant**：在 **网关令牌校验之后的控制面/工具网关**拒绝——tenant **只来自内部令牌**，永不来自模型 JSON。Prompt 防不住。

**证据**：A3 · A9 (a) · G7（R1）

#### 追问

> thread 和 conversation_id 是不是一回事？

#### 再答

产品 conversation 可以映射到 thread，但面试要说清：thread 是**隔离与持久化主键**，不是 UI 气泡 id；一个 thread 可有多次 run。

---

### 题 3 · Q12：四层 Eval

#### 面试官提问（Agent工程师）

> Model / Framework / Harness / Application 各测什么？门禁怎么设？线上「答得不好」先怀疑哪一层？若面试官用「结果/轨迹/成本/对抗」切片你怎么对齐？

#### 候选人解答

**先声明课纲主口径，再映射观测切片，避免各说各话。**

| 课纲层 | 测什么 | 红线例子 | 观测切片对照 |
|--------|--------|----------|--------------|
| Model | 答案/拒答质量 | 该拒不拒 | 结果 |
| Framework | 工具路由、图边、契约 | 缺 expect_tools / 误调 | 轨迹 |
| Harness | 预算、熔断、策略、越权 | 死循环未停、成本爆 | 成本/对抗 |
| Application | 引用、tenant filter、业务合规 | 跨租户、缺 cite | 结果+合规+延迟/$ |

**门禁**：硬门禁一票否决（危险工具、跨租户、holdout≥2pt、成本）；软分数只作参考（A6/O8）。

**定位顺序**：看 Trace span 类型 → 映射到层 → 再改。不要一上来换模型。

**「答得不好」**：先看 Application（有无 cite / 有无 retrieve.filter）和 Framework（工具路径），再看 Model；若有循环 tool 先查 Harness。

**证据**：`curriculum/advanced/A6-eval-otel/` · A9 (e)

---

### 题 4 · Capstone (a)：四键演示

#### 面试官提问（Java高级架构师）

> 作品集怎么证明四键不是写在 Prompt 里？跨租户读 checkpoint 的证据是什么？

#### 候选人解答

- `start_run(internal_token)`：从 HMAC 内部令牌解析 `tenant/user`，生成 `thread/run`，写入 checkpoint 行。
- 日志/DB 行展示四键；`cross_tenant_checkpoint_rows(attacker, thread, run) == 0`。
- 篡改 token body → `bad_signature`。

**证据**：`curriculum/advanced/A9-capstone/` demo 段 (a) · `control_plane/identity.py` · `tests/test_negatives.py`

---

### 题 5 · Capstone (b)：幂等副作用 + Outbox

#### 面试官提问（Java高级架构师）

> 已批准副作用如何保证外部恰好 1？重复 resume / 重复 Outbox 投递呢？和 Temporal Signal 的关系？

#### 候选人解答

1. 审批通过后 `begin_effect` → 幂等键 `tenant:thread:effect`。
2. Outbox 投递；dispatcher **先 find 再 create**。
3. 重复 resume：同一 `external_ref`，`create_calls == 1`。
4. B1：Signal **只记批准**；建单在 Activity；重复 Signal 仍 1 张票。
5. **事务在 Java 领域 API**；Agent/Temporal 不开业务库事务。

**挂科**：Signal/resume 里直接打款；Workflow 当事务。

**证据**：A9 (b) · A2 · B1 demo1/2 · OWNERSHIP.md

#### 追问

> Outbox `pending` 但上游已成功？

#### 再答

同 R1/O1：靠上游按幂等键查询收敛，把 ledger/outbox 标齐；不对齐就再 create。

---

### 题 6 · Capstone (c)(d)(e) 串讲

#### 面试官提问（Agent工程师）

> 60 秒串讲检索 ACL、Loop 熔断、Trace→Eval。各给一个负例。

#### 候选人解答

- **(c)** 检索前按 token 租户+角色过滤；跨租户问不到对方制度；员工看不到 admin 薪资文档。负例：客户端传 tenant 被拒。
- **(d)** 重复 tool 签名 → `circuit_open`；`export_all` → `policy_blocked`；超 max_steps → `budget_exhausted`。
- **(e)** 失败 Trace 脱敏成 fixture；含 `export_all` 进 regression；缺 `retrieve.filter` → `incomplete` **禁写 holdout**。

**证据**：A9 demo (c)(d)(e) · A4 · A1 · A6 · `HOLES.md`

---

## 出题人评分（待填）

> 请直接改本文件打分，群里只留短结论。

| 题 | 分数 (1–5) | 是否过关 | 补洞 |
|----|------------|----------|------|
| Q1 | 5 | 过 | 无；三层落点清，checkpoint≠Durable 追问接住 |
| Q2 | 5 | 过 | 无；伪造 tenant 拒在令牌后控制面，说清了 |
| Q12 | 5 | 过 | 无；两套四层对照 + 定位顺序到位 |
| Capstone (a) | 5 | 过 | 无；四键来自内部令牌 + 跨租户 0 行证据清楚 |
| Capstone (b) | 5 | 过 | 无；Outbox/幂等与 Temporal Signal、Java 事务归属对齐 |
| Capstone (c)(d)(e) | 5 | 过 | 非阻塞：限时串讲可再各补一句「证据文件名」方便白板 |

**整场结论**：**深挖侧 Q1/Q2/Q12 + Capstone (c)(d)(e) 过关**；**架构侧 Capstone (a)(b) 过关**。Mock R2 通过。

**深挖评语（Agent工程师）**：Q1 没把 Runtime 说成 LangGraph；Q2 四键与伪造 tenant 拒层清楚；Q12 先声明口径再映射观测切片，避免和面试官各说各话。(c)(d)(e) 各带负例，和作品集五段对齐。

**架构师评语（Java高级架构师）**：(a) 证明了权限不在 Prompt；(b) 把 resume/Signal/Outbox/领域 API 串成一条正确所有权链。可选附录：限时白板「网关→Agent→Outbox→Java API」。

**建议补洞 PR**：

- [x] 深挖侧评分已填
- [ ] （可选）R2 附录白板图「网关→Agent→Outbox→Java API」

---

## 候选人自检

- [x] Q1 区分 Harness vs Runtime vs LangGraph
- [x] Q2 四键 + 伪造 tenant 拒绝层
- [x] Q12 两套四层对照
- [x] Capstone 五段均落到路径
- [ ] 限时白板画「网关→Agent→Outbox→Java API」（可 R2 附录）
