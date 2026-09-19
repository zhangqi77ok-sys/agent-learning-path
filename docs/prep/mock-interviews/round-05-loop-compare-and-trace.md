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
| R5-Q1 | LLMentor `AgentLoopExecutor` vs dsh-java `ReactLoopAgent` | **已出题 / 待答** |
| R5-Q2 | Session 事件缺 `TOOL_RESULT` 现场排障 | **已出题 / 待答** |

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

_（待填）_

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

_（答后填）_

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

_（待填）_

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

_（答后填）_

---

## 状态

- R5-Q1 / R5-Q2：题面 + 金标已入库；待 agent学生作答  
- 架构延伸（R5-C/D）仍可由 Java高级架构师另开，不阻塞本场深挖  
