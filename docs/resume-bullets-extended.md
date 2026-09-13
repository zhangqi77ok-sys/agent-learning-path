# 简历扩展要点（+12 条）

> 在 [resume-differentials.md](resume-differentials.md) 三条差异化之外，再备 **至少 10 条**可剪贴条目。  
> 用法：按 JD 关键词勾选 4–6 条进「项目经历」，其余留面试储备。  
> 禁止改成纯名词列表；每条保留 **动词 + 机制 + 证据**。

**审稿**：@Java高级架构师 盯 Java/事务/部署口径；@Agent工程师 盯 Runtime/Eval/协议口径。结论写文末表。

---

## 条目清单（12）

### 1. Runtime / Harness 控制面

> 实现 Agent Harness 最小控制面：统一 step 循环、工具白名单、步数/墙钟/调用次数预算，并对重复 tool 签名熔断；死循环在预算内进入 `circuit_open`，支持事件 Replay。

- **证据**：`curriculum/advanced/A1-runtime/`  
- **JD 关键词**：Harness、Runtime、Guardrail、死循环治理  
- **90s 钩子**：Model 只出下一步；策略在图外强制执行。

### 2. 长任务一致性（ledger + Outbox）

> 用 effect ledger + Outbox + 稳定幂等键 `tenant:thread:effect` 处理「外部工具已成功、本地 checkpoint 未写」崩溃；恢复时先查对端再补写，禁止盲重试导致双单。

- **证据**：`curriculum/advanced/A2-long-task/` · Mock R1 O1  
- **JD 关键词**：幂等、Saga/Outbox、断点续跑  
- **挂科对照**：不能说「失败了再调一次工具」。

### 3. Worker 租约与双实例互斥

> 为长任务引入 Worker 租约：同一 run 同时只被一个 Worker 持有；演示双 Worker 抢队列 exactly-once，避免 HITL 跨天扩缩容双跑。

- **证据**：A2 lease · `curriculum/advanced/A8-ha-platform/` demo1  
- **JD 关键词**：分布式、租约、队列

### 4. 多租户身份与审批

> 落地网关内部令牌校验、检索/工具前 ACL、高风险动作审批（审批人身份、过期、版本化快照哈希）；过期或快照不一致则副作用为 0。

- **证据**：`curriculum/advanced/A3-tenant-auth/` · Capstone HITL  
- **JD 关键词**：RBAC、HITL、审计  
- **与①呼应**：四键不来自模型。

### 5. 进阶 RAG（ACL / 版本 / 过期）

> 实现检索前租户与角色过滤、文档生效期与版本 pin（蓝绿别名切换后历史引用可复现）；跨租户与过期文档 hit=0，弱检索可拒绝作答。

- **证据**：`curriculum/advanced/A4-advanced-rag/` · O4/O7  
- **JD 关键词**：RAG、多租户、合规引用

### 6. MCP Registry 防投毒 + 沙箱

> 将 MCP 定位为发现协议而非安全边界：Registry 钉版本与 schema 指纹，描述/schema 漂移 fail-closed；沙箱限制写路径，拦截路径穿越。

- **证据**：`curriculum/advanced/A5-mcp-registry/` · O5  
- **JD 关键词**：MCP、Tool Sandbox、供应链/变更评审  
- **勿与 A2A 混写**（见差异化③ / 条目 11）。

### 7. 四层 Eval 与发布硬门禁

> 拆分 Model/Framework/Harness/Application 评测入口；危险工具、跨租户、成本爆炸、holdout 回退 ≥2pt 硬否决；版本三元组 `eval_set×agent_config×model` 防偷换评测。

- **证据**：`curriculum/advanced/A6-eval-otel/` · O8 · R2 Q12  
- **JD 关键词**：评测、门禁、可观测

### 8. Trace → Bad Case → CI

> 将失败 Trace 脱敏为 fixture 进入 regression；缺 `retrieve.filter` 的 incomplete 禁止写入 holdout，保证坏例下一轮 CI 必跑。

- **证据**：A6 `trace_to_fixture` · A9 (e) · 差异化②  
- **JD 关键词**：OTEL、回归、质量闭环

### 9. 模型网关路由与成本

> 按 `(tenant, task_class, sensitivity, budget_left)` 路由；429/5xx fallback + 熔断，15s 内明确终态；缓存键含 tenant 与 acl_version，跨租户同 query 不串答；超预算禁止打贵模型。

- **证据**：`curriculum/advanced/A7-model-gateway/`  
- **JD 关键词**：成本、路由、多模型、稳定性

### 10. 高可用与租户隔离池

> 用队列+租约+租户并发上限做背压；吵闹租户打满时邻居 P95 不超过基线 2 倍；文档化 SPOF（单 PG/单模型商/单审批队列/单区）及私有化差异。

- **证据**：`curriculum/advanced/A8-ha-platform/` · `DEPLOY.md` · G1  
- **JD 关键词**：高可用、多租户隔离、私有化

### 11. 最小 A2A 委托语义

> 实现 Agent 委托最小集：下行身份、任务级幂等键、deadline 与显式取消；超时/取消后 side_effect=0；与 MCP `call_tool` 分轨，防止孤儿任务。

- **证据**：`curriculum/advanced/B2-a2a/` · `DESIGN.md`  
- **JD 关键词**：Multi-Agent、A2A、协作取消

### 12. Durable Runtime 对照（Temporal）

> 用 Temporal Workflow/Activity/Signal 对照自研队列：Signal 只注入批准意图，建单在幂等 Activity；重复 Signal 外部单据仍为 1；演示 Worker 超管绕过领域 API 的挂科路径并 fail-closed。

- **证据**：`curriculum/advanced/B1-durable-runtime/` · 调研稿 `docs/b1-durable-runtime-research.md`  
- **JD 关键词**：Temporal、Durable Execution、工作流  
- **挂科句打回**：「我们用了 Temporal」——必须讲清 checkpoint 数据 ≠ 续跑、事务在 Java。

---

## 按 JD 速配（勾选建议）

| JD 味道 | 优先条目 |
|---------|----------|
| 平台 / Runtime / Harness | 1, 2, 3, 12 |
| 企业安全 / 私有化 | 4, 5, 6, 10 |
| 评测 / 质量 / 可观测 | 7, 8 |
| 成本 / 稳定性 | 9, 10 |
| 多 Agent | 11, 6 |
| Java 转 Agent（差异化） | 差异化① + 4 + 12 + 2 |

---

## 组合进「一个项目」的写法（Capstone 伞）

若简历只留 **一个** Agent 项目，用 A9 做伞，项目下挂 4–5 条子弹（从上面勾）：

1. 身份四键 + 检索 ACL（4+5）  
2. 幂等 Outbox / Temporal 对照（2+12）  
3. Harness 熔断（1）  
4. Eval 门禁 + 坏例 CI（7+8）  
5. （可选）A2A 或模型网关（11 或 9）

Capstone 路径：`curriculum/advanced/A9-capstone/` · `HOLES.md` 十条对照。

---

## 审稿栏

| 审阅人 | 结论 | 修改意见 |
|--------|------|----------|
| Java高级架构师 | **通过** | 4/10/12 口径准：内部令牌+审批快照、SPOF/私有化、Temporal≠业务事务+超管挂科。非阻塞：条目 4 可半句点出「审批有效期≠执行窗口」（A3 follow-up）。 |
| Agent工程师 | **通过** | 1/2/6/7/8/11 均达标：Harness 熔断、ledger 不盲重试、MCP 非安全边界、四层硬门禁、Trace→CI、A2A 分轨。非阻塞：条目 2 可半句点「started 无 ref」探测（A2 demo1a）；8 与差异化②合并投递时避免复读。 |
