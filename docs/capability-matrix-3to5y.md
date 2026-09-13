# 3–5 年 AI Agent 应用 / 后端能力矩阵（2026）

> 对象：4 年 Java 转 Agent 应用 / Agent 后端 / Agent Infra，对标国内 **3–5 年** 岗，而不是「会调 API + 会画 LangGraph」。  
> 前置：仓库 [Curriculum v2](../../agent-learning-path/docs/curriculum-v2.md) 阶段 ①–④ **只算入门**。本矩阵是进阶主线。  
> 配套：[进阶课纲](curriculum-advanced-3to5y.md) · [深挖题 v2](interview-deep-dive-v2.md) · [过不了就别去面](interview-deep-dive-v2.md#gate) · [进阶 JD 调研](jd-research-advanced-3to5y.md)

## 怎么用

面试官筛的不是名词表，是四件事同时成立：

1. **边界**：tenant / user / thread / run、工具 ACL、检索 ACL，模型改不了。
2. **一次真实（或等价）事故**：越权、重复副作用、死循环烧钱、429 雪崩、HITL 恢复双写，你能讲到根因与修复。
3. **可观测**：OTEL Trace 能从用户请求追到模型、检索、工具、审批。
4. **发布门禁**：四层 Eval 有红线，holdout 掉点不能发。

**只报 LangGraph / MCP / 「我们用了 RAG」= 直接挂。**

---

## JD 来源（公开岗位共性，非 Boss 直聘抓取）

完整具名链接与交集见 **[进阶 JD 调研](jd-research-advanced-3to5y.md)**。此处只留矩阵用摘要。不写薪资均值、不写编制、不伪称「刷过 Boss」。仓库旧文 `docs/boss-jd-research.md` 覆盖入门岗；**3–5 年岗已上移到 Runtime / Harness / 评测闭环 / 多租户 / 私有化**。

| 具名公开来源（猎聘向） | 对 3–5 年的硬信号 |
|------------------------|-------------------|
| 瓴知 · Harness 高级研发 | Runtime State / Checkpoint / Rollback / Commit；四层评测；MCP；Failure Mode；沙箱 |
| 了不起 · Runtime / Harness | 断点续跑、HITL、Tool Sandbox、Guardrail、Tracing + Eval 回归、异步队列 |
| 格创东智 · Agent 后端 | Java+Python；Skill/运行时；MQ/向量；评测治理；**私有化部署**与项目隔离 |
| 信华信 · Agent 应用开发 | Framework/Runtime 二次开发；Skill/Memory/MCP；能独立上线 |
| 财开 · 智能体（浙财数智） | LangGraph/RAG/MCP/Skills；上下文工程；应用落地 |
| 辅助：小红书 Harness / 天鹅到家 Runtime 架构师 / 字节 Agent 研发 | Serverless 与权限穿透；`Model+Harness=Agent`；上下文工程与 ownership |

**市场口径（不编数字）**：Agent 侧 Python/Go；网关与政企/工业交付常要 Java；硬关键词是 **Runtime State、长任务续跑、Sandbox、Eval 回归、MQ+向量+私有化**。

---

## 总表

| ID | 维度 | 期望深度（3–5 年） | 可演示产物 | 典型挂科 | 模块 | 深挖 |
|----|------|-------------------|------------|----------|------|------|
| D1 | Runtime / Harness | 能分层控制面与执行面，而不是「一个图」 | 自研最小 Harness：Loop + Policy + Budget + Replay | 把框架当 Runtime | [A1](curriculum-advanced-3to5y.md#a1) | [Q1](interview-deep-dive-v2.md#q1) |
| D2 | 耐久长任务 | Checkpoint / 队列 / 取消 / 补偿可恢复 | PG checkpoint + 取消传播 + 补偿记录 | MemorySaver 上生产 | [A2](curriculum-advanced-3to5y.md#a2) | [Q4](interview-deep-dive-v2.md#q4) [Q6](interview-deep-dive-v2.md#q6) |
| D3 | 多租户安全 | 隔离键强制注入；RBAC + 审批 + 审计 | 跨租户读 0 行；审批写审计日志 | Prompt 里写「不要越权」 | [A3](curriculum-advanced-3to5y.md#a3) | [Q2](interview-deep-dive-v2.md#q2) [Q3](interview-deep-dive-v2.md#q3) |
| D4 | 进阶 RAG | 混合检索 + 重排 + 版本/过期 + 检索 ACL | 租户过滤 + 过期文档不进上下文 | 检索后再用 Prompt 过滤 | [A4](curriculum-advanced-3to5y.md#a4) | [Q7](interview-deep-dive-v2.md#q7) |
| D5 | MCP / A2A / 注册中心 / 沙箱 | 协议 + 治理，不是起一个 MCP server | Registry、schema 版本、沙箱策略 | 工具直连生产库 | [A5](curriculum-advanced-3to5y.md#a5) | [Q3](interview-deep-dive-v2.md#q3) [Q8](interview-deep-dive-v2.md#q8) |
| D6 | Eval / 观测 / 门禁 | 四层评测 + OTEL + 发布红线 | Trace→Bad Case→回归必跑 | 只有 LLM-as-Judge 总分 | [A6](curriculum-advanced-3to5y.md#a6) | [Q12](interview-deep-dive-v2.md#q12)–[Q14](interview-deep-dive-v2.md#q14) |
| D7 | 模型网关 / 成本 | 按租户路由、预算、429 降级 | 路由决策进 Trace；超预算可拒绝 | 全局一个模型硬编码 | [A7](curriculum-advanced-3to5y.md#a7) | [Q9](interview-deep-dive-v2.md#q9) [Q10](interview-deep-dive-v2.md#q10) |
| D8 | 分布式高并发 | 队列、无状态 Runtime、隔离与背压 | 压测下 P95 与取消仍正确 | 进程内线程池当平台 | [A8](curriculum-advanced-3to5y.md#a8) | [Q6](interview-deep-dive-v2.md#q6) [Q11](interview-deep-dive-v2.md#q11) |
| D9 | Java 网关 → Python Agent 身份 | 可信身份单向注入，Agent 不可抬权 | 伪造 header 被拒；工具带下行身份 | Agent 自己解析用户 JWT | [A3](curriculum-advanced-3to5y.md#a3) [A5](curriculum-advanced-3to5y.md#a5) | 口述题 G7 |
| D10 | 系统设计 | 20 分钟画得完、说得清 SPOF 与一个 SLO | 组件图 + 故障域 + 门禁 | 只画 Agent 节点 | [A9](curriculum-advanced-3to5y.md#a9) | [Q15](interview-deep-dive-v2.md#q15) |

---

<a id="d1"></a>

## D1. Runtime / Harness

**期望深度**

- 能背诵并落地公开 JD 口径：`Model + Harness = Agent`。模型只负责下一步决策；**Loop、状态机、断点、上下文压缩、Session/Memory 生命周期、预算、策略、沙箱、Replay** 都在 Harness。
- **Runtime** 是执行与隔离平面：进程/容器生命周期、队列领取、租户资源配额、与 K8s/Serverless 的对接。Harness 可以跑在 Runtime 里，但不是一回事。
- 能说明为何「源码级用过一种框架」仍不够：框架给了图，**没给你多租户控制面**。

**可演示产物**

- 一个薄 Harness：`step` 循环、工具网关、预算、策略钩子、把 LangGraph（或自研状态机）当作可替换执行器。
- 一份对照表：LangGraph 已提供 vs 你必须自建（租户键、预算、ACL、outbox、OTEL 语义约定）。

**挂科模式**：把 `graph.invoke` 叫 Runtime；说不清 Supervisor 挂了子 Agent 的状态谁管。

**链接**：模块 [A1](curriculum-advanced-3to5y.md#a1) · 题 [Q1](interview-deep-dive-v2.md#q1)

---

<a id="d2"></a>

## D2. 耐久长任务（Checkpoint / 队列 / 取消 / 补偿）

**期望深度**

- 检查点是**恢复语义**，不是日志：tenant+thread 定位工作项，run 定位一次执行，节点副作用必须可跳过。
- Postgres（或等价）检查点：多副本、HITL 跨进程、kill -9 可续。`MemorySaver` 只属于阶段 ④ 课堂。
- 取消是协作式的：信号进入 Runtime → 当前 step 可见 → 子 Agent/工具截止 → 已发生副作用走补偿，而不是「杀线程」。
- 队列与执行分离：控制面接受任务，Worker 拉 run；重试与重放用同一幂等键。

**可演示产物**：审批通过后的外部写走 Outbox；重复 resume / 重复投递副作用恰好 1；取消后 5s 内无新 tool span。

**挂科模式**：resume 再跑一遍 writer；用 HTTP 超时当取消；补偿靠人工改库。

**链接**：模块 [A2](curriculum-advanced-3to5y.md#a2) · 题 [Q4](interview-deep-dive-v2.md#q4) [Q5](interview-deep-dive-v2.md#q5) [Q6](interview-deep-dive-v2.md#q6)

---

<a id="d3"></a>

## D3. 多租户安全（RBAC / 审批 / 审计）

**期望深度**

- 四个隔离键（见 [Q2](interview-deep-dive-v2.md#q2)）是主键，不是日志字段。模型、检索 query、工具参数**都不能改 tenant_id**。
- 工具可见性按 `(tenant, role, tool, risk_level)`；高风险工具必须 HITL。审批人、时间、输入摘要进审计表。
- ABAC 加分：文档密级、部门、项目。RBAC 不够时能讲清为什么，而不是上一个「超级管理员 Agent」。

**可演示产物**：租户 A 的 thread 读不到 B 的 checkpoint；未授权工具不出现在模型可见 schema；审批拒绝无副作用。

**挂科模式**：网关验了登录，Agent 内部用 `tenant_id = payload.get("tenant")`。

**链接**：模块 [A3](curriculum-advanced-3to5y.md#a3) · 题 [Q2](interview-deep-dive-v2.md#q2) [Q3](interview-deep-dive-v2.md#q3)

---

<a id="d4"></a>

## D4. 进阶 RAG

**期望深度**

- 阶段 ③ 的切分+检索+引用是前置。3–5 年要：**混合检索、重排、query 改写、文档版本与过期、引用忠实、检索 ACL/RLS**。
- 能讲「什么时候不上 RAG」：短时效政策、必须精确的制度条款、权限极敏感的名单，应走结构化查询或拒答。
- 索引与生成解耦：embedding 模型升级要能重建；过期/废止文档不得只靠 Prompt「请忽略」。

**可演示产物**：同一问句在两租户召回不同集合；过期文档 recall=0；弱检索降级为拒答而不是幻觉。

**挂科模式**：向量库无 filter；重排只为刷分；说不清 chunk 失败与权限失败的差异。

**链接**：模块 [A4](curriculum-advanced-3to5y.md#a4) · 题 [Q7](interview-deep-dive-v2.md#q7)

---

<a id="d5"></a>

## D5. MCP / A2A / Tool Registry / 沙箱

**期望深度**

- MCP 解决**工具协议与发现**；A2A（及 JD 里并列的 ACP）解决**跨 Agent 委托与 Agent Card**。两者都不等于安全边界。
- Registry：工具名、schema 版本、owner、风险级、租户白名单、健康检查。下线版本必须让旧 run 失败可见，而不是静默改语义。
- 沙箱：代码执行 / 浏览器 / 文件 IO 进 gVisor / Firecracker / 等价隔离；网络与密钥最小授权。内嵌 Python tool 直连生产库 = 事故。

**可演示产物**：同一 Agent 经 Registry 调 MCP 工具；schema 不兼容被拒；沙箱逃逸用例被策略拦下（演示用 harmless 文件写入即可）。

**挂科模式**：「我们上了 MCP所以安全」；A2A 被讲成 HTTP 互调。

**链接**：模块 [A5](curriculum-advanced-3to5y.md#a5) · 题 [Q3](interview-deep-dive-v2.md#q3) [Q8](interview-deep-dive-v2.md#q8) · 口述 [G2](curriculum-advanced-3to5y.md#oral)

---

<a id="d6"></a>

## D6. Eval / 可观测 / 发布门禁

**期望深度**

四层评测与瓴知等公开 JD 对齐，三份文档必须用同一套名字（Model / Framework / Harness / Application）。另有面试常用切片：**结果 / 轨迹 / 成本 / 对抗**——与主口径对照见 [Q12](interview-deep-dive-v2.md#q12)，两套都要能讲。

主口径表：

| 层 | 测什么 | 门禁直觉 |
|----|--------|----------|
| Model | schema 遵从、拒答、单次忠实 | 换模型时先过本层 |
| Framework | 图/状态机契约、检查点恢复、节点幂等 | 恢复后 effects 不双写 |
| Harness | 预算、熔断、ACL、compaction、超时 | 死循环必停；越权必拒 |
| Application | 业务任务成功、引用、成本、延迟、合规 | holdout 不回退才能发 |

- OTEL：一次用户请求一条 Trace，span 覆盖 gateway / retrieve / model / tool / hitl / outbox。
- 线上失败必须能**快照脱敏后重放**，并进入回归集（[Q14](interview-deep-dive-v2.md#q14)）。

**可演示产物**：四层报告 + 一条红线配置；故意坏工具被 Harness 层拦住且 Application 层记失败原因，而不是「模型不行」。

**挂科模式**：20 条固定题调到 95 分；Trace 只有 printf。

**链接**：模块 [A6](curriculum-advanced-3to5y.md#a6) · 题 [Q12](interview-deep-dive-v2.md#q12)–[Q14](interview-deep-dive-v2.md#q14) · 口述 [G4](curriculum-advanced-3to5y.md#oral)

---

<a id="d7"></a>

## D7. 模型网关 / 成本

**期望深度**

- 网关做：鉴权后的模型路由、密钥托管、超时、429/5xx 分类、fallback、token/人民币预算、缓存。
- 路由键：`(tenant, task_class, sensitivity, budget_left)`，决策必须进 Trace。
- 成本是产品约束：超预算是明确失败或降级，不是默默换贵模型。

**可演示产物**：租户 A 走小模型、B 走强模型；注入 429 后 fallback 或明确失败；日报 token。

**挂科模式**：客户端写死模型名；无限重试 429；说不清 cache 命中会不会串租户。

**链接**：模块 [A7](curriculum-advanced-3to5y.md#a7) · 题 [Q9](interview-deep-dive-v2.md#q9) [Q10](interview-deep-dive-v2.md#q10)

---

<a id="d8"></a>

## D8. 分布式高并发

**期望深度**

- Agent 请求是长尾、占槽、可重入的。按同步 QPS 设计线程池会先死在工具等待。
- 要会：工作队列、租约、单 run 互斥、背压、隔离池（租户级或任务级）、无状态 Worker。
- 能指出 SPOF：单 Postgres、单模型网关、单队列分区、单 HITL 审批人。

**可演示产物**：双 Worker 抢同一 run 只有一个执行；压测下取消仍正确；熔断后新 run 快速失败。

**挂科模式**：`asyncio` 当分布式；「上 K8s 就高可用」。

**链接**：模块 [A8](curriculum-advanced-3to5y.md#a8) · 题 [Q11](interview-deep-dive-v2.md#q11) [Q15](interview-deep-dive-v2.md#q15)

---

<a id="d9"></a>

## D9. Java 网关 → Python Agent 可信身份

**期望深度**（Java 转岗的差异化，必须能画）

```
用户 ──SSO/JWT──► Java 网关（鉴权、会话、业务 ACL）
                    │  签发短时内部令牌（tenant, user, roles, trace_id, exp）
                    │  mTLS / 内网只收网关
                    ▼
              Python Agent Runtime
                    │  只信内部令牌，不信模型/工具回包里的身份字段
                    ▼
              工具网关 / MCP ──原身份下行──► 业务 API
```

- Agent 是**无特权执行器**。抬权只发生在 Java 网关。
- 内部令牌受众（aud）= Agent 服务，TTL 分钟级，不可当用户 JWT 转发到公网。
- 工具调用带 `acting_user` / `tenant`；业务 API 再验一次，防 Python 被 RCE 后横移。

**可演示产物**：curl 绕过网关直打 Agent 被拒；篡改 tenant claim 验签失败；工具日志能对上网关 audit。

**挂科模式**：Python 重解析用户 JWT；把用户 token 塞进 Prompt；MCP 里写死 admin。

**链接**：模块 [A3](curriculum-advanced-3to5y.md#a3) [A5](curriculum-advanced-3to5y.md#a5) · 口述 [G7](curriculum-advanced-3to5y.md#oral)

---

<a id="d10"></a>

## D10. 系统设计（20 分钟口述）

**期望深度**：每道口述题必须同时给出 **组件图、一个 SPOF、一个定量 SLO**（课程建议值，不是行业统计）。见 [课纲口述题](curriculum-advanced-3to5y.md#oral) 与 [Q15](interview-deep-dive-v2.md#q15)。

**可演示产物**：一页架构 + 故障域 + 门禁表，能对着 Trace 讲「上次事故卡在哪一层」。

**挂科模式**：只画 researcher → writer；SLO 用「尽量快」。

---

## 与阶段 ①–④ 的关系

| 已会（前置） | 3–5 年必须补上 |
|--------------|----------------|
| Chat API / 中转站 / `.env` | 模型网关、路由、预算、429 |
| 手写 Loop、超时重试 | 多维预算、熔断、Outbox、补偿 |
| 单库检索 + 引用 | 混合检索、重排、版本过期、RLS |
| LangGraph + MemorySaver + interrupt | PG checkpoint、隔离键、跨进程 HITL |
| （v2 阶段 ⑤⑥ 仍是占位） | MCP 治理、四层 Eval、OTEL、门禁、多租户控制面 |

阶段 ⑤⑥ 与作品集不再按 v2 入门口径验收，统一收到 [进阶课纲](curriculum-advanced-3to5y.md)。

---

## 作品集与口试硬门槛

- Capstone 五段演示见 [A9](curriculum-advanced-3to5y.md#capstone)（隔离键 / Outbox / 检索 ACL / 预算熔断 / Trace→Eval）。
- 课堂 Demo 的 [10 个死亡坑](curriculum-advanced-3to5y.md#holes) 必须能逐条反驳。
- 面试前过 [过不了就别去面](interview-deep-dive-v2.md#gate)；O10 事故叙事必过。

---

## 转岗建议（给 Java 四年经验）

你的可迁移资产：网关鉴权、幂等、Outbox、分布式锁、熔断、RBAC、审计。缺口通常在：**Harness 分层、检索 ACL、Eval 门禁、上下文工程**。作品集优先做 [A9 Capstone 五段演示](curriculum-advanced-3to5y.md#capstone)，不要再堆第三个 Chatbot。
