# Mock Interview Round 4 · 2026-09-19

## 元信息

| 项 | 内容 |
|----|------|
| 候选人 | agent学生（对标 3–5 年 Agent 应用 / Harness 工程） |
| 深挖面试官 | Agent工程师 |
| 架构面试官 | Java高级架构师（本场后半接归属链 / 审批 / 事件溯源） |
| 形式 | 真机项目口试 + 全文入库；禁止空概念 |
| 本机证据根 | `E:\LLMentor` · `E:\deepseek-harness-java` |
| 仓库课纲对照 | `projects/hotplug-harness` · `03-modules/A*` · `04-frontier/B*` |
| 硬约束（maxzq） | 出题人必须给**标准答**；答方必须引用**真实路径**；查痛点与经历，不编造 |

## 项目审查摘要（面试官会前笔记）

### `E:\LLMentor`（馒头大模型实战课工程）

- 定位：**应用层实验台**（Spring AI / LangChain4j / AgentScope / MCP / RAG / Agent / Workflow）。
- 控制面线索：`ai-framework/spring-ai-agentx-core/.../AgentLoopExecutor.java`（`maxRounds` / `ToolCallExecutor` / deferred tools）；`agent/dodo-agent/.../SimpleReactAgent.java` 等业务 Agent。
- 面试用法：讲「业务 Agent 怎么拼」；**不要**把它说成生产级多租户 Harness。

### `E:\deepseek-harness-java`（DeepSeek Harness Java / dsh-java）

- 定位：**单实例 Agent Harness 运行时**（Java 17 · Spring Boot 3.3 · DDD 六边形）。
- 主证据：
  - Loop：`.../domain/agent/service/run/ReactLoopAgent.java`（kick / turn / step / cancel / wakeDriver）
  - 工具唯一入口：`.../domain/tool/service/ToolCallExecutor.java`（解析 → tool_call 事件 → 运行时审批 → PRE Hook → 执行 → POST Hook → tool_result）
  - 插件生命周期 API：`...-api/.../IHarnessPlugin*Api.java`
- 会攻击的痛点（候选人须主动认账）：
  1. 运行时审批 / gate **默认策略过松**时，对话可直达高危工具（shell / 写文件）。
  2. Shell 类工具若近零命令白名单，安全几乎全靠审批与容器。
  3. 步数护栏 ≠ 签名熔断 / token 成本账本。
  4. 单实例定位：缺一等公民多租户 RAG ACL / Eval 门禁时要对齐 JD 讲清楚「缺什么、补在哪一层」。

---

## 议程

| # | 题 | 侧 | 状态 |
|---|----|----|------|
| Q1 | ReactLoopAgent：kick/turn/step + 协作式 cancel + Inbox 重入 | 深挖 | **已答 / 已评分** |
| Q2 | ToolCallExecutor 唯一入口 · 审批/Hook DENY · 前缀路由 | 深挖 | **已答 / 已评分** |
| Q3 | 插件卸载回收（工具/提示/Hook）与 ClassLoader 隔离 | 深挖 | **已答 / 已评分** |
| Q4 | LLMentor `AgentLoopExecutor` vs dsh `ReactLoopAgent` 边界 | 深挖 | 待出 |
| G1 | 归属链：Gateway → Harness → Outbox/领域 API | 架构 | 待 Java高级架构师接 |
| O9/O10 | 审批与事故七段 | 架构 | 待接 |

---

## 逐题记录

### Q1 · ReactLoopAgent 驱动模型

#### 面试官提问（Agent工程师）

> 打开 `E:\deepseek-harness-java\...\ReactLoopAgent.java`。用自己的话讲 `kick` / `turn` / `step` 各自干什么；`cancel` 时为什么是协作式停在安全点而不是杀线程？若 Inbox 在 turn 中又来了新消息，会怎样？必须点到类/方法名。

#### 候选人解答（agent学生）

- **kick**：异步驱动 `while` 消费 inbox。
- **turn**：一次用户回合（≤50 step）；首步 claim 消息；有工具则 `midTurnContinuation` 续步。
- **step**：流式 LLM + 可选 tool；有工具返回 `null` 表示续步。
- **cancel**：只设 abort 标志（+可选清 inbox）；流 `onNext` / 工具 executor 在安全点停，**不杀线程**，保证 `turnEnd` / 事件收尾。
- **turn 中新消息**：`append` inbox + `wakeRequested`；当前 turn 结束后 kick 重入；abort 中 wakeup 改 `NEXT_TURN`。
- **自报证据**：`ReactLoopAgent.kick/turn/step/cancel/send/wakeDriver`。

#### 面试官标准答（Agent工程师 · 金标）

**分层（控制面所有权）**

| 方法 | 职责 | 不该做什么 |
|------|------|------------|
| `kick` / `wakeDriver` | 驱动器：Inbox 非空则进入 Running，异步泵 turn，直到空或 abort | 不直接调模型、不直接执行工具副作用 |
| `turn` | 一次用户可见回合：打开 turn、循环 step、关闭 turn、发 turn 结束事件 | 不绕过 ToolCallExecutor 执行工具 |
| `step` | 单次「模型流式输出 →（可选）工具计划」；有 tool_calls 则续步，无则收敛 | 不自己 `Runtime.exec` |

**协作式 cancel（生产痛点）**

- 杀线程会导致：半截 SSE、tool_call 无 tool_result、事件日志悬挂、外部副作用状态不明。
- 正确做法：`cancel(cause, keepInbox)` 置位 abort → 当前 LLM chunk / 工具执行在**安全点**退出 → 仍写 `turnEnd` / `agent/cancelled` 类事件，保证回放与审计闭合。
- 这与「恰好一次副作用」同一家族：先保证**可观测、可恢复**，再谈重试。

**Inbox 重入**

- 当前 turn 不抢插到半截 step 中间改语义；消息入队 + wake；turn 尾再 kick。
- abort 中的 wakeup 必须降级到 `NEXT_TURN`，避免与收尾竞态。

**企业追问（本场可加分）**

- 50 step / 续写次数防的是什么？（失控循环、max_tokens 截断续写，不是成本账本。）
- 若工具已成功、事件未落盘就挂了——和 O1 幂等题如何衔接？（点到 ledger / 外部幂等键，而不是「再问模型」。）

#### 评分

| 维度 | 分 | 评语 |
|------|----|------|
| 机制正确性 | 9/10 | kick/turn/step、协作 cancel、Inbox 重入均对齐源码 |
| 证据锚定 | 8/10 | 方法名齐全；可再显式提 turnEnd/事件收尾 |
| 生产痛点 | 8/10 | 提到安全点与事件收尾；未主动对比「杀线程」事故 |
| **总分** | **8.5/10** | 过关；补强：退出条件（有工具续步 vs 无关 turn）+ 事件闭合 |

**缺口（下一轮要补进口述）**：turnEnd/事件收尾保证回放一致；step「有工具 → 续步 / 无工具 → 关 turn」退出条件说死。

---

### Q2 · ToolCallExecutor 唯一入口

#### 面试官提问（Agent工程师）

> 打开 `E:\deepseek-harness-java\...\ToolCallExecutor.java`：
> 1. 为什么所有工具必须过它（而不能让 Model/插件自己副作用）？
> 2. 走一遍：解析 → `tool_call` 事件 → 运行时审批 → PRE Hook → 执行 → POST Hook → `tool_result`。
> 3. PRE Hook DENY 与审批 DENY 分别如何落库/回放？
> 4. 若存在 `plugin__*` / `mcp__*`（或等价命名空间）前缀，它们在路由与审批矩阵上起什么作用？
>
> 答完必须带类/方法名；允许说「源码里前缀是 X，我本地 grep 到的路径是 …」。**禁止**只背「要有鉴权」。

#### 候选人解答（agent学生）

- **证据**：`ToolCallExecutor.runGroup/shouldBlock/checkApproval/appendToolCall`；`PluginToolDefinition`；`McpToolAdapter`；`MatrixRuntimeApprovalGate`。
- **唯一入口**：全工具必须过 Executor，才能保证事件成对 + 审批不旁路。
- **流水线（以源码为准）**：parse → PRE → 审批 → `tool_call` → execute → POST → 有序 `tool_result`（指出源码里 PRE 在审批前，与部分注释顺序不一致）。
- **DENY**：PRE DENY → `HOOK_BLOCKED`；审批 DENY → `APPROVAL_REQUIRED`；均写合成失败结果、不执行真工具。
- **前缀**：`plugin__` / `mcp__` 为 Registry 限定名，用于路由、按全名审批、卸载回收。

#### 面试官标准答（Agent工程师 · 金标 · 先公布供对照）

**为何唯一入口**

- Model 只提出 tool_calls；**Harness 拥有副作用边界**。
- `ToolCallExecutor` 集中：参数解析、事件成对、审批、Hook、并发/取消、结果顺序。
- 绕过它 = 审计断裂 + 审批失效 + 回放无法重建。

**流水线（以 `ToolCallExecutor` 方法体为准；javadoc 若写反以代码为准）**

1. `argumentsParser.parse` 解析参数  
2. PRE Hook（`shouldBlock` / PRE_TOOL_USE）：BLOCK/DENY → 跳过真实执行，合成失败（如 `HOOK_BLOCKED`）  
3. `checkApproval` / `RuntimeApprovalGate`（如 `MatrixRuntimeApprovalGate`）：DENY → **不执行**，合成失败（如 `APPROVAL_REQUIRED`）  
4. `appendToolCall` 记录 `tool_call` 事件（含序号，供 result 关联）——具体插入点以本机方法体为准，但**成对**是硬约束  
5. 调用 registry 中的工具实现（`plugin__*` / `mcp__*` 经 `PluginToolDefinition` / `McpToolAdapter`）  
6. POST Hook（只观察）  
7. 按派发顺序写 `tool_result`（并行时防交叉乱序）

> 金标修正：候选人指出「PRE 在审批前」——与方法体行序一致；面试时要能解释「注释/文档过期时以代码为真相」。

**DENY 两种的差别（面试常混）**

| 来源 | 语义 | 落库 |
|------|------|------|
| 运行时审批 DENY | 策略/人工未批准 | 合成失败 result，文案含 requires approval |
| PRE Hook DENY/BLOCK | 策略脚本/安全钩子拦截 | 合成失败 result，原因 HOOK_BLOCKED 类 |

共同点：**绝不漏 result**，否则下一轮模型与回放器看到悬挂 tool_call。

**前缀 / 命名空间**

- 用于区分内置工具 vs 插件 vs MCP 适配工具，便于审批矩阵按来源路由、卸载时按前缀回收注册。
- 候选人须用本机 `Select-String`/`rg` 给出**实际**前缀字符串与注册点；若与文档不一致，以源码为准并说明。

**生产痛点（必须能讲）**

- 审批门若默认 allowAll，唯一入口也挡不住「能调到 shell」。
- Hook 未注入时源码直接放行 → 配置错误即裸奔。
- 并行工具必须保序落 result，否则多工具对话回放错位。

#### 评分

| 维度 | 分 | 评语 |
|------|----|------|
| 机制正确性 | 9/10 | 唯一入口、成对事件、两种 DENY 合成失败均正确 |
| 证据锚定 | 9/10 | Executor/Gate/Plugin/MCP 类名扎实 |
| 源码诚实度 | 9.5/10 | 敢于纠正「PRE vs 审批」顺序，对齐方法体 |
| 生产痛点 | 7.5/10 | 未主动攻「Gate 默认放行 / Hook 未注入即裸奔」 |
| **总分** | **8.8/10** | 过关偏强；补强默认安全策略与卸载回收 |

**缺口**：默认 allow / Hook 空注入时的事故面；下一题强制讲卸载回收。

---

### Q3 · 插件卸载回收
#### 面试官提问（Agent工程师）

> 场景：生产上刚热更新了一个带 `shell_execute` 包装的 Java 插件，发现 prompt 投毒，要立刻卸载。
> 1. 从哪个 API/用例开始卸？（点 `IHarnessPlugin*Api` 或等价 command）
> 2. 卸载后必须从哪些注册表消失：工具名（含 `plugin__` 前缀）、系统提示增量、PRE/POST Hook、ClassLoader 是否可 GC？
> 3. 若正在跑的 turn 里已经 `tool_call` 了该插件工具，unload 与 in-flight 执行谁赢？会不会留下悬挂 `tool_result`？
> 4. 对照 `E:\LLMentor`：那边的 Agent 实验台有没有同等「卸载回收」？没有的话，面试怎么诚实表述两项目边界？
>
> 必须带本机路径/类名；讲不清 in-flight 直接判痛点题不及格。

#### 候选人解答（agent学生）

1. **入口**：`POST /api/harness/plugins/{id}/uninstall` → `ManagePluginNode.UNINSTALL`（先 `runtime.stop` 再 `registry.uninstall`）；紧急可用 disable/`STOP`。
2. **回收**：`JavaPluginRuntimeManager.stop` → `context.close` 逆序回收 `plugin__` 工具 / Hook / prompt / 订阅 + ClassLoader unload + `hookRegistry.unregisterAll`。
3. **in-flight**：注册面 unload 赢；`stop` 不与 in-flight 联动（abort 属 `Agent.cancel`）。已 `appendToolCall` 应靠执行失败闭合 `tool_result`，但 stop 不等待 inFlight——**生产痛点：先 cancel Agent 再卸**。主动认账。
4. **边界**：LLMentor 无对等热卸载（仅 `ToolCircuitBreakerHook`）；课仓 ≠ Harness 运行时。

#### 面试官标准答（Agent工程师 · 金标）

**目标**：卸载 = **撤销能力注册**，不是只删 jar 文件。

1. **入口**：插件命令 API（安装/激活/停用/卸载）→ domain 插件生命周期；停用应先于物理删除。紧急路径可用 disable/STOP。
2. **回收清单**（缺一算泄漏）：Tool registry（含 `plugin__` 限定名）、system prompt/skill 片段、Hook 订阅、子进程/Node bridge、ClassLoader 强引用去除。
3. **in-flight**：
   - 已进入 `ToolCallExecutor`：应跑完或协作取消，并**仍写 tool_result**（成功/失败/ABORTED），禁止悬挂
   - 未开始的同名调用：registry miss → 合成失败，而不是 NPE
   - **运维顺序**：先 `Agent.cancel`（或等价 abort）再 unload；若 runtime.stop 不等 inFlight，必须在 runbook 写明，否则事件可能断裂
4. **与 LLMentor 边界**：课内验证 ReAct/MCP/RAG；热插拔回收与审批矩阵以 dsh-java / `projects/hotplug-harness` 为准。

**痛点**：只删文件不卸注册 → 幽灵工具；unload 时杀线程 → 事件不成对；stop 与 in-flight 无联动且不先 cancel → 半截副作用。

#### 评分

| 维度 | 分 | 评语 |
|------|----|------|
| API/生命周期 | 9/10 | uninstall/stop/disable 路径与类名清楚 |
| 回收清单 | 9/10 | 工具/Hook/prompt/CL 都点到 |
| in-flight 痛点 | 9/10 | 主动承认 stop 不等 inFlight，给出「先 cancel 再卸」 |
| 项目边界 | 9/10 | LLMentor 无热卸载，表述诚实 |
| **总分** | **9.0/10** | 痛点题过关；可再补「registry miss 合成失败」防 NPE 一句 |

---

## 本场纪律



1. 证据只承认：本机路径、本仓库 `projects/hotplug-harness`、已合 PR 文档。  
2. 课程工程（LLMentor）与 Harness（dsh-java）**角色不同**，混为一谈直接扣「架构归属」分。  
3. 出题人标准答与候选人答并列入库；打分后改状态表。

## 状态

- Q1：已完成（8.5）  
- Q2：已完成（8.8）  
- Q3：已完成（9.0）；深挖三题均过关  
- 架构侧：**交接** Java高级架构师接 G1/O9/O10（归属链/审批/事件溯源），续写本文件或 `round-04b`  
