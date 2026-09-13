# 进阶课纲：3–5 年 AI Agent 应用 / 后端（2026）

> **前置**：仓库 Curriculum v2 阶段 ①–④（`curriculum/stage-01` … `stage-04`）只算入门。会调 API、会写 Loop、会 RAG 引用、会 LangGraph + `MemorySaver` + `interrupt`，**不够投 3–5 年岗**。  
> 配套：[能力矩阵](capability-matrix-3to5y.md) · [深挖题 v2（15 题）](interview-deep-dive-v2.md) · [过不了就别去面（10 口试）](interview-deep-dive-v2.md#gate) · [进阶 JD 调研](jd-research-advanced-3to5y.md)

v2 阶段 ⑤⑥ 与作品集占位**不再按入门口径验收**，能力并入本课纲 A5 / A6 / A7 / A9。

---

## 市场对这门课的要求（不编薪资）

公开猎聘向 JD 的交集（具名来源见 [JD 调研](jd-research-advanced-3to5y.md)）：

- **Runtime / Harness**：Runtime State、Checkpoint / Rollback / Commit、长任务续跑、HITL。
- **工具安全**：Sandbox、Guardrail、Skill 注册与版本、MCP/A2A。
- **Eval / 回归 / OTEL**：失败可复现，发布有红线。
- **企业落地**：Java + MQ + 向量库 + **私有化部署**、项目隔离、审计。
- **所有权**：能独立扛一条链路，而不是「参与过 Demo」。

字节跳动类 JD 额外强调：云原生与架构、**上下文工程**、评测/可观测、独立项目 ownership。框架名（LangGraph / Eino）只是门槛。

---

<a id="holes"></a>

## 当前仓库 LangGraph + HITL Demo 的 10 个死亡坑

阶段 ④ 交付（`MemorySaver` + `interrupt` + `effects`）对课堂够用，**拿去当面 3–5 年等于自爆**。面试官会按下面 10 条拆：

| # | 死亡坑 | 课堂现状 | 3–5 年必须补到 |
|---|--------|----------|----------------|
| 1 | Checkpoint ≠ 业务一致性 | 状态回写成功就当「做完了」 | 外部写走 [执行账本 / Outbox](interview-deep-dive-v2.md#q5)；工具成功但 checkpoint 失败见 [口试 O1](interview-deep-dive-v2.md#o1) |
| 2 | 无 Worker 租约 | 单进程内存图 | 单 `run_id` 互斥租约；双 Worker 不能双跑 |
| 3 | HITL 无审批人身份 / 过期 | `resume={'approved': True}` | 审批人、过期、快照哈希、拒绝审计 |
| 4 | 租户只在 State 里 | 模型可写的字段当隔离 | 四键由网关注入，RLS 强制，见 [Q2](interview-deep-dive-v2.md#q2) |
| 5 | MCP 无工具投毒防御 | 信任 `list_tools` 描述 | 白名单、schema 指纹、钉版本，见 [O5](interview-deep-dive-v2.md#o5) |
| 6 | RAG 无 ACL / 版本 | 单库 TF-IDF + 引用 | 检索前 ACL、过期/版本、历史可复现，见 [O4](interview-deep-dive-v2.md#o4) [O7](interview-deep-dive-v2.md#o7) |
| 7 | 无 Eval 门禁 | 无黄金集版本、无 holdout | 四层 Eval + 硬门禁，见 [Q12](interview-deep-dive-v2.md#q12) [O8](interview-deep-dive-v2.md#o8) |
| 8 | 无成本 / P99 | 只看「能跑通」 | 租户预算、P95/P99、429 降级 |
| 9 | 无 Spring 集成 | Python 单飞 | Java 网关身份、MQ/SSE、事务归属，见 [O9](interview-deep-dive-v2.md#o9) [G7](#g7) |
| 10 | 作品集无法证明生产 | 无事故、无 Trace 闭环、无负例 | Capstone 五段 + 一篇结构化事故（[O10](interview-deep-dive-v2.md#o10)） |

**过关定义**：能对着这 10 条逐条指出课堂代码缺什么、你补了什么、用哪条故障注入证明。

---

## 模块总表

建议实现目录（尚未建，评审后再进仓库）：`curriculum/advanced/A1-…`。

| ID | 模块 | 主要深挖 | 口试 / 口述 |
|----|------|----------|-------------|
| A1 | Runtime 控制面 | [Q1](interview-deep-dive-v2.md#q1) [Q11](interview-deep-dive-v2.md#q11) | [O6](interview-deep-dive-v2.md#o6) |
| A2 | 长任务一致性 | [Q4](interview-deep-dive-v2.md#q4) [Q5](interview-deep-dive-v2.md#q5) [Q6](interview-deep-dive-v2.md#q6) | [O1](interview-deep-dive-v2.md#o1) [O2](interview-deep-dive-v2.md#o2) [O3](interview-deep-dive-v2.md#o3) |
| A3 | 企业租户 / RBAC / 审批 / 审计 | [Q2](interview-deep-dive-v2.md#q2) [Q8](interview-deep-dive-v2.md#q8) | [G3](#g3) [G7](#g7) |
| A4 | 进阶 RAG：混合 / 重排 / 版本过期 | [Q7](interview-deep-dive-v2.md#q7) | [O4](interview-deep-dive-v2.md#o4) [O7](interview-deep-dive-v2.md#o7) |
| A5 | MCP / A2A + Registry / 沙箱 | [Q3](interview-deep-dive-v2.md#q3) [Q8](interview-deep-dive-v2.md#q8) | [O5](interview-deep-dive-v2.md#o5) [G2](#g2) |
| A6 | 四层 Eval + OTEL + 门禁 | [Q12](interview-deep-dive-v2.md#q12)–[Q14](interview-deep-dive-v2.md#q14) | [O8](interview-deep-dive-v2.md#o8) [G4](#g4) |
| A7 | 模型网关 / 路由 / 成本 | [Q9](interview-deep-dive-v2.md#q9) [Q10](interview-deep-dive-v2.md#q10) | [G5](#g5) |
| A8 | 高可用 / 分布式 Agent 平台 | [Q6](interview-deep-dive-v2.md#q6) [Q11](interview-deep-dive-v2.md#q11) | [O9](interview-deep-dive-v2.md#o9) |
| A9 | Capstone：多租户企业 Agent 控制面 | [Q15](interview-deep-dive-v2.md#q15) | [G1](#g1) [O10](interview-deep-dive-v2.md#o10) |

SLO 数字均为**课程建议验收值**，不是行业统计。

---

<a id="a1"></a>

## A1. Runtime 控制面

**业务场景**  
业务线要把「报销助手 / 知识助手 / 工单助手」接到同一套执行底座：统一 Loop、预算、策略、Replay，而不是每个项目复制一份 `graph.invoke`。

**硬概念**

- `Model + Harness = Agent`：模型只出下一步；Harness 管 Loop、compaction、预算、Guardrail、Replay。
- Runtime ≠ Harness：Runtime 管领取、隔离、生命周期、配额。
- 控制面（创建 thread/run、策略、路由）与数据面（step 执行）分离。

**实现交付**

- 薄 Harness SDK：`start_run` / `step` / `cancel` / `replay`。
- 执行器可替换（LangGraph 或自研状态机）。
- 对照表：框架已有 vs 自建（写入 README）。

**故障注入**：无限 tool 意图；重复相同 tool 签名；超预算后禁止再开一轮。

**指标 / SLO**：死循环在 ≤ 8 step 或 ≤ 30s 墙钟内进入 `circuit_open`；预算耗尽后新 tool span = 0。

**面试映射**：[D1](capability-matrix-3to5y.md#d1) · [Q1](interview-deep-dive-v2.md#q1) [Q11](interview-deep-dive-v2.md#q11)

---

<a id="a2"></a>

## A2. 长任务一致性

**业务场景**  
跨天审批的采购 / 出差：工具可能已调用外部系统，进程会被杀，用户会取消，审批会重放。

**硬概念**

- Checkpoint 恢复图，**不恢复外部世界**。
- 执行账本（ledger）才是副作用的真相源；幂等键 `(tenant, thread, effect)`。
- 取消协作式；补偿是 Saga，不是 `ROLLBACK`。
- Worker **租约**：同一 `run_id` 同时只被一个 Worker 持有。

**实现交付**

- Postgres checkpointer（按 tenant 分区或 RLS）。
- Outbox + dispatcher；补偿表。
- `cancel_requested` 传播到工具 deadline。

**故障注入**：tool 成功后杀进程再写 checkpoint（[O1](interview-deep-dive-v2.md#o1)）；双 Worker 抢 run；取消发生在 HTTP 进行中。

**指标 / SLO**：重复 resume 外部 mock = 1；取消后 5s 内无新 tool；kill -9 后 30s 内可 resume。

**面试映射**：[D2](capability-matrix-3to5y.md#d2) · [Q4](interview-deep-dive-v2.md#q4)–[Q6](interview-deep-dive-v2.md#q6) · [O1](interview-deep-dive-v2.md#o1)–[O3](interview-deep-dive-v2.md#o3)

---

<a id="a3"></a>

## A3. 企业租户 / RBAC / 审批 / 审计

**业务场景**  
SaaS 知识助手：多公司、多角色；高风险动作（导出、对外发送）必须人批；审计要能对到人。

**硬概念**

- 四隔离键不可由模型改写。
- Java 网关签发短时内部令牌；Python 只信内部令牌。
- 审批：审批人身份、过期、基于**版本化快照**（防审批期间数据被换）。
- 审计不可变：谁、何时、对哪条 thread/run、看见什么摘要。

**实现交付**

- Spring 网关 stub：登录 → 内部 JWT（`tenant,user,roles,trace,exp,aud`）。
- Agent 拒绝无签 / 错 aud / 过期；伪造 tenant 失败。
- 审批记录表 + 过期自动 `approval_expired`。

**故障注入**：绕过网关直打 Agent；篡改 claim；过期后 resume；错误角色调高风险工具。

**指标 / SLO**：越权工具调用 = 0（评测集）；审批过期后副作用 = 0。

**面试映射**：[D3](capability-matrix-3to5y.md#d3) [D9](capability-matrix-3to5y.md#d9) · [Q2](interview-deep-dive-v2.md#q2) [Q8](interview-deep-dive-v2.md#q8) · [G7](#g7)

---

<a id="a4"></a>

## A4. 进阶 RAG（混合 / 重排 / 版本过期）

**业务场景**  
制度与产品文档按月废止；两家租户文档不能串；监管要能回答「当时依据哪一版」。

**硬概念**

- 混合检索 + 重排；弱检索拒答。
- **ACL 在检索前**；索引/缓存/长期记忆都带 tenant。
- 文档不可变版本；过期不进召回。
- 历史回答绑定 `kb_version`，重建索引不改写旧版本。

**实现交付**

- 元数据：`tenant_id, doc_id, version, effective_from, expires_at, acl`。
- 检索 API 不接受客户端 tenant。
- 双构建 + 原子切换（蓝绿别名）。

**故障注入**：跨租户投毒文档；过期文档；切换版本时旧 task 仍引用旧 version。

**指标 / SLO**：跨租户 hit = 0；过期文档 recall = 0；历史 replay 引用 version 一致。

**面试映射**：[D4](capability-matrix-3to5y.md#d4) · [Q7](interview-deep-dive-v2.md#q7) · [O4](interview-deep-dive-v2.md#o4) [O7](interview-deep-dive-v2.md#o7)

---

<a id="a5"></a>

## A5. MCP / A2A + Registry / 沙箱

**业务场景**  
工具平台化：业务系统经 MCP 暴露；跨团队 Agent 用 A2A 委托；代码解释器必须进沙箱。

**硬概念**

- MCP = 协议与发现，**不是**安全边界。
- Registry：名字、schema 指纹、钉版本、风险级、租户白名单、变更评审。
- 描述被静默改写 = 工具投毒；默认 fail-closed。
- 沙箱：网络/文件系统/密钥最小授权。

**实现交付**

- 最小 MCP server + Registry（版本钉死）。
- schema hash 不匹配则拒绝。
- 一个沙箱工具（写 `/tmp` 白名单）；禁网。

**故障注入**：改 tool description 诱骗导出；schema 加字段；沙箱写工作区外。

**指标 / SLO**：未评审 schema 变更拦截率 100%（注入集）；沙箱逃逸 = 0。

**面试映射**：[D5](capability-matrix-3to5y.md#d5) · [Q3](interview-deep-dive-v2.md#q3) · [O5](interview-deep-dive-v2.md#o5) · [G2](#g2)

---

<a id="a6"></a>

## A6. 四层 Eval + OTEL + 门禁

**业务场景**  
Prompt「线下 +3%」想发版；安全与 P99 不能让步；线上 Bad Case 要隔夜进回归。

**硬概念**

- 四层：Model / Framework / Harness / Application（与矩阵 [D6](capability-matrix-3to5y.md#d6) 同名）。面试若被问「结果/轨迹/成本/对抗」，按 [Q12 对照表](interview-deep-dive-v2.md#q12) 映射，不要否认另一套切片。
- holdout 锁定；版本三元组：`eval_set × agent_config × model`。
- 硬门禁 > 软分数：越权、危险调用、成本爆炸一票否决。
- OTEL 全链路；失败快照脱敏后 replay。

**实现交付**

- 四份评测入口 + 门禁配置。
- `trace_to_fixture`（PII 剥离）。
- 影子流量 / 金丝雀说明（可单机模拟百分比路由）。

**故障注入**：线下分涨但危险工具误开；holdout 被误写入 few-shot；Trace 缺 retrieve.filter。

**指标 / SLO**：硬门禁失败不得发；holdout 相对基线回退 ≥ 2pt 阻断；新 Bad Case 下一轮 CI 必跑。

**面试映射**：[D6](capability-matrix-3to5y.md#d6) · [Q12](interview-deep-dive-v2.md#q12)–[Q14](interview-deep-dive-v2.md#q14) · [O6](interview-deep-dive-v2.md#o6) [O8](interview-deep-dive-v2.md#o8) · [G4](#g4)

---

<a id="a7"></a>

## A7. 模型网关 / 路由 / 成本

**业务场景**  
多租户不同套餐；主模型 429；财务要按租户看 token。

**硬概念**

- 路由键：`(tenant, task_class, sensitivity, budget_left)`。
- 429/5xx 分类、抖动退避、熔断、fallback。
- 缓存键含 tenant 与权限版本。

**实现交付**

- 网关：路由表、预算计数、fallback、决策进 Trace。
- 日/月预算耗尽返回明确错误或约定降级。

**故障注入**：429 序列；跨租户同 query 缓存；预算耗尽仍打贵模型。

**指标 / SLO**：429 后 15s 内达到明确终态；跨租户缓存串答 = 0；超预算贵模型调用 = 0。

**面试映射**：[D7](capability-matrix-3to5y.md#d7) · [Q9](interview-deep-dive-v2.md#q9) [Q10](interview-deep-dive-v2.md#q10) · [G5](#g5)

---

<a id="a8"></a>

## A8. 高可用 / 分布式 Agent 平台

**业务场景**  
私有化 + 中心 SaaS 都要：多 Worker、队列、背压、单区故障可讲清。

**硬概念**

- 长尾请求不按同步线程池设计。
- 队列 + 租约 + 背压 + 租户隔离池。
- 指出 SPOF：单 PG、单模型供应商、单审批队列、单区。

**实现交付**

- 至少两个 Worker 抢队列的演示。
- 租户级并发上限。
- 部署草图：K8s Deployment + PVC/托管 PG + 模型网关；私有化差异一节。

**故障注入**：一个租户打满；PG 主库暂停；模型网关全 503。

**指标 / SLO**：隔离池生效时租户 B 的 P95 劣化有上限（课程：B 的 P95 不超过基线 2 倍）；队列积压可观测。

**面试映射**：[D8](capability-matrix-3to5y.md#d8) · [O9](interview-deep-dive-v2.md#o9) · [G1](#g1)

---

<a id="a9"></a>
<a id="capstone"></a>

## A9. Capstone：多租户企业 Agent 控制面

**业务场景**  
把 A1–A8 收成一个可演示控制面：Java 鉴权 → Python Harness → 检索/工具/HITL → Outbox → Trace → Eval。这是作品集的**唯一主项目**。

**硬概念**：见 [Q15](interview-deep-dive-v2.md#q15)。能讲清 10 个死亡坑各补了哪一块。

**实现交付（五段演示，缺一不可）**

| ID | 演示 | 最低证据 |
|----|------|----------|
| (a) | 隔离键 thread / run / tenant / user | 日志或 DB 行展示四键；跨租户读 checkpoint = 0 行 |
| (b) | 幂等的已批准副作用 + Outbox | 重复 resume / 重复投递，外部 mock 恰好 1 |
| (c) | 检索 ACL / RLS | 跨租户 query hits=0；本租户可引用回答 |
| (d) | Loop 预算与熔断 | 死循环工具在预算内 `circuit_open` |
| (e) | Trace → Bad Case → Eval 重放 | 从一条失败 Trace 生成脱敏 fixture 且 CI 必跑 |

**故障注入**：五段各至少 1 个负例脚本（可 `pytest`）。

**指标 / SLO（Capstone 建议红线）**

- 跨租户越权（检索+工具）= 0
- 已批准副作用恰好 1
- 只读问答 P95 < 8s（本地/中转站环境需在 README 声明硬件与模型）
- 危险工具误调用 = 0（注入集）

**面试映射**：全部 Q + [O10](interview-deep-dive-v2.md#o10) + 下方 7 道口述。

---

<a id="oral"></a>

## Java 架构师口述系统设计（7 题）

每题口头必须同时给出：**组件图、1 个 SPOF、1 个定量 SLO**。只点框架名不及格。

<a id="g1"></a>

### G1. 企业知识助手端到端

- **图**：Java 网关、Harness/Runtime、模型网关、PG+向量、Registry/沙箱、Outbox、OTEL、Eval。
- **SPOF 例**：单区 Postgres 或单模型供应商。
- **SLO 例**：只读问答 P95 < 8s；跨租户越权 = 0。
- **映射**：[Q15](interview-deep-dive-v2.md#q15) · A9

<a id="g2"></a>

### G2. 工具平台：MCP vs 内嵌 Tool

- **图**：Registry、MCP server、内嵌适配器、沙箱、变更评审。
- **决策**：跨团队/多语言/需发现 → MCP；低延迟强一致本域 → 内嵌，但仍走同一 ACL。
- **SPOF 例**：Registry 不可用导致全工具失败（要有缓存的钉版本副本）。
- **SLO 例**：未钉版本的 schema 变更拦截 100%（注入集）。
- **映射**：A5 · [O5](interview-deep-dive-v2.md#o5)

<a id="g3"></a>

### G3. HITL Checkpoint 不重复副作用

- **图**：interrupt → 审批服务（身份/过期/快照）→ Outbox → 外部 API。
- **SPOF 例**：审批队列单实例无持久化。
- **SLO 例**：批准重放 100 次，外部副作用 = 1。
- **映射**：A2 · [Q5](interview-deep-dive-v2.md#q5) · [O3](interview-deep-dive-v2.md#o3)

<a id="g4"></a>

### G4. Eval 发布门禁

- **图**：四层 runner、holdout 仓、门禁、金丝雀、回滚。
- **SPOF 例**：评测与线上共用被污染的集。
- **SLO 例**：硬门禁失败不得发；holdout 回退 ≥ 2pt 阻断。
- **映射**：A6 · [O8](interview-deep-dive-v2.md#o8)

<a id="g5"></a>

### G5.（加分）模型路由与成本

- **图**：租户套餐、路由表、预算、fallback、成本账。
- **SPOF 例**：单一上游。
- **SLO 例**：超预算贵模型调用 = 0；429 后 15s 内明确终态。
- **映射**：A7

<a id="g6"></a>

### G6.（加分）长期记忆 / 隐私 / 过期

- **图**：工作记忆 vs 长期记忆；租户隔离；TTL/遗忘；用户导出/删除。
- **硬点**：记忆写入也要 ACL；过期与「被遗忘」必须从向量索引删除，不只是标记。
- **SPOF 例**：记忆库无备份或无租户键。
- **SLO 例**：删除请求后 T+24h 检索命中该记忆 = 0（课程约定）。
- **映射**：A3 · A4

<a id="g7"></a>

### G7.（加分）Java 网关 → Python Agent 可信身份

- **图**：见 [D9](capability-matrix-3to5y.md#d9)。
- **硬点**：事务与抬权在 Java；Agent 无特权；工具下行身份；业务 API 再验。
- **SPOF 例**：内部签发密钥单点泄漏（要轮换）。
- **SLO 例**：绕过网关直打 Agent 拒绝率 100%（测试集）。
- **映射**：A3 · [O9](interview-deep-dive-v2.md#o9)

---

## 建议节奏（转岗，非日历 KPI）

| 顺序 | 内容 | 完成信号 |
|------|------|----------|
| 0 | 对照 10 个死亡坑写差距清单 | 每条有「缺/补/如何证」 |
| 1 | A1 + A2 | 租约 + PG checkpoint + Outbox |
| 2 | A3 + A7 + G7 | 身份链 + 预算 |
| 3 | A4 + A5 | ACL RAG + Registry 指纹 |
| 4 | A6 + A8 | 四层门禁 + 双 Worker |
| 5 | A9 五段 + 事故叙事 O10 | 可 20 分钟口述 G1 |

每周至少一次可运行提交（本地即可）。**不要**再开第三个 Chatbot。

---

## 验收（给评审角色）

| 角色 | 看什么 |
|------|--------|
| Java 架构师 | 7 道口述的图 + SPOF + SLO；D9 身份链；死亡坑 1/2/3/9 |
| Agent 工程师 | 15 道深挖 + 10 道「过不了就别去面」；四层 Eval 同名 |
| 学生 | Capstone (a)–(e) 负例全绿；无密钥入库 |
