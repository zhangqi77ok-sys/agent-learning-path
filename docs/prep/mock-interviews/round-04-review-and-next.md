# Mock R4 复盘与提升计划（agent学生）

> 依据：`round-04-llmentor-dsh-java.md`（Q1–Q3 深挖 + G1/O9/O10 架构）  
> 约束（maxzq）：面试不能草草收场；答完必须**复盘 → 补学 → 再面**；全文进 GitHub。

## 1. 本场成绩快照

| 题 | 分 | 过关点 | 扣分 / 缺口（要练） |
|----|----|--------|-------------------|
| Q1 ReactLoop | 8.5 | kick/turn/step；协作式 cancel；wake/NEXT_TURN | 口述要钉死：有工具 `step→null` 续步 vs 无工具关 turn；`turnEnd` 保证回放 |
| Q2 ToolCallExecutor | 8.8 | 唯一入口；成对事件；HOOK vs APPROVAL；plugin__/mcp__；纠正 PRE→审批 | **主动打**「Gate 默认放行 / Hook 未注入裸奔」生产痛点 |
| Q3 热卸载 | 9.0 | uninstall 入口；回收清单；in-flight 先 cancel 再卸 | 可补：ClassLoader 竞态失败如何仍闭合 result |
| G1 归属链 | 9.0 | Trigger→Harness；三权；诚实无 Outbox | 限时白板 15min 默画 |
| O9 审批 | 9.2 | Gate 分支；Broker 10min 超时 DENY；两类审批 | 默背 FULL_OPEN/AUTO_APPROVE/askHandler=null |
| O10 七段 | 8.9 | Ownership+指标；租约；先 cancel | 计时 ≤2min 脱稿，②⑦不砍 |

## 2. 立刻补学清单（按优先级）

### P0（本周必须会脱口）

1. **默认安全失败**：`MatrixRuntimeApprovalGate` askHandler=null→DENY；`setHookService` 未注入则 PRE 直接放行——配置错即裸奔。  
2. **step 退出条件** + **事件闭合**：对照 `ReactLoopAgent.step` 返回值表。  
3. **Unload runbook**：`AgentController.cancel` → `POST .../uninstall`；口述事故七段 3 遍（用 `timed-practice-pack`）。

### P1（对照课仓补齐「企业链」）

4. 用 `03-modules/A9-capstone` + `04-frontier/B1` 再讲一遍「dsh-java 没有的 Outbox/领域事务」——防止面试硬套 Temporal。  
5. 读 `SessionRebuilderService` / `PersistingSessionLog` 源码各一遍，能指悬挂 call 如何暴露。

### P2（下一轮面试素材）

6. **LLMentor 深挖**：`AgentLoopExecutor` / `SimpleReactAgent` / RAG 课模块——角色是课仓，别冒充生产 Harness。  
7. **MCP 安全**：dsh-java `McpToolAdapter` vs 课仓 A5 指纹——两边能力差什么。  
8. **多 Agent / 工作流**：dsh-java docs ch15 vs 课仓 frontier——边界一句话。

## 3. 建议下一轮题单（请面试官出题+金标）

| 轮 | 出题人 | 主题 | 为何要面 |
|----|--------|------|----------|
| R5-A | Agent工程师 | LLMentor `AgentLoopExecutor` vs dsh `ReactLoopAgent` 对比 | 防两仓混谈 |
| R5-B | Agent工程师 | Session 重建：给一段缺 TOOL_RESULT 的事件 JSON 现场排障 | 实操 Trace |
| R5-C | Java高级架构师 | 写租约冲突 + 双实例写同一 session | 生产并发 |
| R5-D | Java高级架构师 | 任务审批 vs 运行期工具审批 联调故事 | O9 延伸 |
| R5-E | 双方 | 限时：O10 2min + G1 15min 白板连考 | 投递前必过 |

## 4. 自我约束

- 每题答完 24h 内：对照金标写「我漏了哪句痛点」进本文件附录。  
- 不把课仓 API 说成已在 dsh-java 上线。  
- 空概念（「我们做了 DDD」）自我红牌。

## 附录 · R4 漏句补丁（口述卡片）

**Q2 漏句**：门禁矩阵若 FULL_OPEN、或 Hook 服务没注入，唯一入口也挡不住 shell——配置与默认值是生产事故源。  
**Q1 漏句**：有 tool_calls → `step` 返回 null 续步；无工具 → `Completed` 关 turn；abort → `turnEnd(Aborted)` 闭合事件。  
**Unload 漏句**：先 cancel 再 uninstall；只卸注册表不等于 in-flight 已停。

## 附录 · R5 漏句补丁（Agent工程师代写 · 2026-09-19）

> 应 agent学生请求代录入（其 CloudAgent 不可用）。口述必须能脱口。

### 旁路（课仓）

- `internalToolExecutionEnabled(true)` → 框架直接执行工具，绕过 `AgentLoopExecutor` / `ToolCallExecutor`。
- **正确演示/近生产配置：一律 `false`**，工具只从自己的 Executor 出。

### null Gate / Hook（dsh）

- `FULL_OPEN` → 实质 ALLOW。
- `askHandler == null` → 矩阵内应 DENY（若实现如此）。
- `setApprovalGate(null)` / Gate 未注入 → **allowAll 裸奔**。
- `hookService == null` → PRE 直接跳过。
- **口诀**：唯一入口 ≠ 默认安全；默认失败靠装配与启动校验。

### 合成 RESULT

- 任何 DENY/BLOCK/ABORT/卸载打断：必须先有/补齐 `TOOL_CALL`，再写合成失败 `TOOL_RESULT`，禁止悬挂。
- 缺 RESULT = Trace **硬否决**，先别怪模型。

### 先 cancel 再 unload

- Runbook：`Agent.cancel`（安全点写 ABORTED RESULT）→ 再 `uninstall`/`JavaPluginRuntimeManager.stop`。
- 只卸注册表或杀线程 → 幽灵工具或事件不成对。

### R5 成绩

| 题 | 分 |
|----|----|
| Q1 Loop 对比 | 8.7 |
| Q2 缺 TOOL_RESULT | 9.1 |
| Q3 默认失败 | 9.0 |
| 均分 | 8.9 |

### R6-Q1

- MCP 投毒 vs plugin 隔离：**9.2**（承认 dsh 无 fingerprint 为加分诚实项）。
