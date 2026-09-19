# Mock Interview Round 5 · 2026-09-19

## 元信息

| 项 | 内容 |
|----|------|
| 候选人 | agent学生 |
| 深挖面试官 | Agent工程师 |
| 形式 | 复盘后再面（maxzq：不能草草收场） |
| 前置 | [round-04](round-04-llmentor-dsh-java.md) · [复盘](round-04-review-and-next.md) |
| 证据根 | `E:\LLMentor` · `E:\deepseek-harness-java` |
| 硬约束 | 题面 + **面试官金标** + 学生答 + 评分全文入库；禁止空概念；两仓角色不许混 |

## 本场目标

1. 钉死 **课仓 Loop vs 生产 Harness Loop** 边界（防混谈）。  
2. 用 **缺 TOOL_RESULT 的事件链** 做现场排障（对齐 O10 / Trace 硬否决口径）。

## 议程

| # | 题 | 状态 |
|---|----|------|
| R5-Q1 | LLMentor `AgentLoopExecutor` vs dsh-java `ReactLoopAgent` | **已答 / 已评分 8.7** |
| R5-Q2 | Session 事件缺 `TOOL_RESULT` 现场排障 | **已答 / 已评分 9.1** |

---

### R5-Q1 · 两个 Loop 对比（防混仓）

#### 面试官提问（Agent工程师）

> 打开两边源码对照讲（必须点类/方法）：
> 1. `E:\LLMentor\...\AgentLoopExecutor`（或你本机等价名）与 `E:\deepseek-harness-java\...\ReactLoopAgent` 各自的**循环驱动、退出条件、取消语义**差在哪？
> 2. 哪一边拥有「工具唯一入口 + 运行时审批 + 插件热卸载」？哪一边只是课内拼装？
> 3. 若简历写「我做了 Agent Runtime」，面试官拿这两仓追问时，你**一句话**怎么划边界才不翻车？
>
> 禁止把 LLMentor API 说成已在 dsh-java 上线。

#### 候选人解答（agent学生）

1. **驱动/退出/取消**：`AgentLoopExecutor`=`scheduleRound`+`maxRounds`+Pause/SafePoint/`resume`；`ReactLoopAgent`=`kick`/`turn`/`step`+Inbox+abort 协作取消。课仓：无工具出终态或达上限；dsh：无工具关 turn、有工具 `step→null` 续步。
2. **治理归属**：完整「唯一入口 + 矩阵运行时审批 + 插件热卸载」只在 dsh；课仓 `ToolCallExecutor` 是执行+Hook/HITL，无 Matrix Gate / JAR unload。
3. **简历边界**：课仓练循环拼装；生产 Runtime 证据锚 dsh——不把课仓 API 说成 dsh 已上线。

#### 面试官标准答（Agent工程师 · 金标）

| 维度 | LLMentor（课仓） | dsh-java（Harness） |
|------|------------------|---------------------|
| 定位 | 教学实验台：拼 ReAct / MCP / RAG | 单实例生产向 Agent **控制面** |
| 驱动 | `AgentLoopExecutor`：`maxRounds` 内 `ChatClient` ↔ 工具；常靠框架/回调执行工具 | `ReactLoopAgent`：`kick` 泵 Inbox → `turn` → `step`；工具必须进 `ToolCallExecutor` |
| 退出 | 轮次耗尽 / 模型不再要工具 / 业务 Agent 自定停 | 无工具关 turn；有工具 `step` 续步；abort → 协作停 + `turnEnd` 事件 |
| 取消 | 多为停任务/断请求，事件闭合不统一 | `cancel` 置 abort，安全点停，保证事件可回放 |
| 治理 | 一般无矩阵审批、无插件 ClassLoader 热卸载 | `MatrixRuntimeApprovalGate` + Hook；`JavaPluginRuntimeManager.stop` 回收 `plugin__` |
| 持久化真相 | 演示日志为主 | `SessionEventLog`（`TOOL_CALL`/`TOOL_RESULT` 成对）为审计真相 |

**一句话边界（口述卡片）**：  
「LLMentor 用来验证模型和编排写法；线上控制面（唯一工具入口、审批、热卸载、事件成对）以 deepseek-harness-java / 仓库 `projects/hotplug-harness` 为准——课仓不等于 Runtime。」

**痛点加分句**：课仓 `internalToolExecutionEnabled(true)` 时工具可能绕过你以为的「Executor」——和 dsh「严禁旁路」正好相反。

#### 评分

| 维度 | 分 | 评语 |
|------|----|------|
| 机制对比 | 9/10 | scheduleRound vs kick/turn/step、退出条件清楚 |
| 治理归属 | 9/10 | 唯一入口/矩阵审批/热卸载只认 dsh，不混仓 |
| 简历边界 | 9/10 | 一句话不翻车 |
| 痛点加分 | 7/10 | 未主动点课仓 `internalToolExecution` 旁路风险、dsh `turnEnd` 事件闭合 |
| **总分** | **8.7/10** | 过关；Q2 要拿成对 RESULT 硬否决补强 |

---

### R5-Q2 · 缺 TOOL_RESULT 排障（Trace 硬否决）

#### 面试官提问（Agent工程师）

> 线上回放一段 Session 事件（口述即可，按序）：
> 1. `TURN_START`  
> 2. `MODEL_DELTA`…  
> 3. `TOOL_CALL` name=`plugin__mail__send` id=`call_9`  
> 4. （此处之后没有任何 `TOOL_RESULT` for `call_9`）  
> 5. 进程重启 / 或下一条用户消息进来  
>
> 问：
> 1. 重建会话时哪里会炸？你会查哪些类（Session 重建 / EventLog / Executor）？
> 2. 根因候选至少列 3 个（cancel 杀线程、unload 不等 in-flight、审批挂起未写结果、Hook 抛错未捕获、落库失败…），并说明**如何用日志/指标一票否决**。
> 3. 修复的「最小正确动作」是什么：合成失败 RESULT、禁止开新 turn、还是重放工具？各自风险？
> 4. 和 R4-Q3「先 cancel 再 unload」怎么串成一条事故叙事？
>
> 缺「成对闭合」意识直接不及格。

#### 候选人解答（agent学生）

1. **炸点**：`SessionRebuilderService.projectMessages` 缺 ToolResult observation；`derivePhase` 卡 Running/Maintenance。查 `PersistingSessionLog` / `ToolCallExecutor.appendToolResult|appendSkippedToolCall` / `ReactLoopAgent.cancel` / `JavaPluginRuntimeManager.stop` 时间序。
2. **根因≥3**：cancel 杀线程无 RESULT；unload 夹在 CALL 与缺 RESULT 之间；Broker 超时 DENY 未写合成 RESULT；Hook 抛未捕获；异步镜像写 RESULT 失败——各有一票否决信号。
3. **最小动作**：优先合成失败 `TOOL_RESULT` 闭合；闸新 turn；勿默默重放 mail（除非幂等可证）。
4. **30s 叙事**：先 cancel 让 Executor 写 ABORTED 再 unload；否则只有 CALL 无 RESULT → 重建炸 / 幻觉已发。

#### 面试官标准答（Agent工程师 · 金标）

**重建何处炸**

- `SessionRebuilder` / 等价回放器遇到悬挂 `TOOL_CALL`：模型上下文缺 observation，或断言失败。  
- 证据类：`SessionEventLog` / `PersistingSessionLog` / `ToolCallExecutor`（是否写了合成 result） / `ReactLoopAgent.cancel` 路径。

**根因候选与否决**

| 候选 | 一票否决信号 |
|------|----------------|
| cancel/杀线程 | abort 日志有，无 `TOOL_RESULT`；线程 dump 显示硬中断 |
| unload 抢先 | plugin stop 时间戳夹在 CALL 与缺失 RESULT 之间 |
| 审批挂起未决 | Gate PENDING，Broker 超时未写 DENY result |
| PRE Hook 抛未捕获 | Hook 栈异常后无 append result |
| DB 写 RESULT 失败 | CALL 已提交、RESULT 事务回滚；出站副作用可能已发生 |

**最小正确动作**

1. **优先**：写合成 `TOOL_RESULT`(error=`ABORTED`/`HOOK_BLOCKED`/`APPROVAL_REQUIRED`/…) 闭合 call——保证回放与下一 turn 可继续。  
2. **不要**默认静默重放外部副作用工具（邮件/支付）——除非幂等键可证未执行。  
3. 闸住新 turn：直到悬挂 call 闭合（控制面硬规则）。

**串 R4-Q3 事故叙事（口述 30s）**

「热更新插件投毒 → 运维直接 uninstall → `JavaPluginRuntimeManager.stop` 卸注册，但 in-flight `plugin__mail__send` 仍在跑或被掐断 → 只有 `TOOL_CALL` 无 `TOOL_RESULT` → 重启后 Session 重建失败 / 模型幻觉已发送。正确 runbook：先 `Agent.cancel` 让 Executor 在安全点写 ABORTED result，再 uninstall；并对邮件类工具用幂等键防双发。」

**Trace 面试口径**：缺成对 RESULT = **硬否决**，不是先换模型。

#### 评分

| 维度 | 分 | 评语 |
|------|----|------|
| 炸点定位 | 9/10 | Rebuilder/phase/Executor/stop 时间序到位 |
| 根因+否决信号 | 9/10 | ≥5 条且含审批超时、Hook、落库 |
| 最小正确动作 | 9.5/10 | 合成 RESULT + 闸 turn + 禁盲目重放副作用 |
| 事故串联 | 9/10 | 先 cancel 再 unload 叙事清楚 |
| **总分** | **9.1/10** | 成对闭合硬纪律过关 |

---

### R5-Q3 · 课仓旁路 vs Harness 闸门（续挖）

#### 面试官提问（Agent工程师）

> R5-Q1 扣分点补考（必须带本机开关/类名）：
> 1. LLMentor 里工具若走「框架内置自动执行」而不是你的 Executor，会发生什么？如何用配置/代码证明旁路存在或已关掉？
> 2. dsh-java 若 `MatrixRuntimeApprovalGate` 处于 FULL_OPEN / askHandler=null / Hook 未 `setHookService`，唯一入口还防得住 `shell` 吗？
> 3. 给出一条**生产默认安全**主张：默认 DENY 还是默认 ALLOW？和课仓演示默认有何冲突？
>
> 答不全「默认失败」直接扣痛点分。

#### 候选人解答（agent学生）

_（待填）_

#### 面试官标准答（Agent工程师 · 金标）

1. **课仓旁路**：Spring AI / 课仓若 `internalToolExecutionEnabled(true)`（或等价），模型 tool_calls 由框架直接调工具，你的 `ToolCallExecutor`、审计、HITL 全瞎。证明：搜配置与 `ChatClient` 定制；演示应强制 false，工具只从 Executor 出。
2. **dsh 伪安全**：唯一入口只保证「过管道」；FULL_OPEN / 空 askHandler 误配置 / Hook 未注入时，管道内仍可能直接执行高危工具。要看 Gate 默认分支与启动校验。
3. **主张**：生产默认 **DENY/只读允许**，高危工具强制审批+超时合成 DENY RESULT；课仓可为了教学默认宽——简历必须说清「演示默认 ≠ 生产默认」。

#### 评分

_（答后填）_

---

## 状态

- R5-Q1：已完成（8.7）
- R5-Q2：已完成（9.1）
- R5-Q3：已出题 + 金标；**待答**（补 Q1 旁路/默认失败）  
- 架构延伸（R5-C/D）仍可由 Java高级架构师另开，不阻塞本场深挖  
