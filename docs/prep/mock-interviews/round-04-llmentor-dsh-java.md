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
| G1 | 归属链：Trigger/API → Harness → Tool/审批 → Session Event Log | 架构 | **已出题 / 待答** |
| O9 | 运行期审批：Matrix Gate + Broker 挂起/放行 | 架构 | **已出题 / 待答** |
| O10 | 事件溯源事故七段：不成对 tool_result / 写租约 / 重建 | 架构 | **已出题 / 待答** |

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


---

### G1 · 归属链（Java高级架构师）

#### 面试官提问（Java高级架构师）

> 对着 `E:\deepseek-harness-java`（可对照课仓 `03-modules/A9-capstone` / `04-frontier/B1-*`）画一条**副作用归属链**：
> 1. 用户一条消息从哪个 Trigger/API 进系统？经过哪些层到达 `ReactLoopAgent`？
> 2. **谁拥有**「能不能调工具」的决策？谁拥有「工具副作用已发生」的事实？谁拥有「会话可回放」的事实？三者能否是同一组件？
> 3. 若要对标企业里「Gateway 抬权 / Harness 编排 / Java 领域事务」三分法：dsh-java 里哪一段相当于 Gateway、哪一段是 Harness、哪一段**还没有**（或故意不做）领域 Outbox？面试怎么诚实讲边界，而不是硬套 Temporal？
>
> 必须带模块路径/类名；空谈「我们用了 DDD」不及格。

#### 候选人解答（agent学生）

（待答）

#### 面试官标准答（Java高级架构师 · 金标）

**目标**：分清**抬权入口、编排执行、外部世界写入、会话真相**四类归属，禁止混称。

1. **进线（Trigger）**：REST/SSE 控制台或 `IGatewayStreamApi` 一类触发层 → case/app → domain `ReactLoopAgent.kick/turn/step`。Trigger **不**直接调工具实现。
2. **三权分立（对本仓库）**
   - **工具是否可执行**：`ToolCallExecutor` + `MatrixRuntimeApprovalGate`（+ Hook PRE）——决策在门禁，不在模型。
   - **工具副作用是否发生**：具体 `ToolDefinition.execute`（内置/`plugin__`/`mcp__`）——只有过门禁后的真实 execute 才算「外部世界变了」。
   - **会话可回放真相**：`SessionEventLogService.append`（`TOOL_CALL`/`TOOL_RESULT` 等，`SessionEventType`）——审计与重建以事件为准，不以内存 Agent 状态为准。
3. **对标企业三分法（诚实边界）**
   - **≈ Gateway**：鉴权/会话打开/流式出口（trigger + session registry），负责「谁可以开跑」。
   - **≈ Harness**：`ReactLoopAgent` + `ToolCallExecutor` + 审批 Broker——负责编排、预算/取消、门禁。
   - **领域 Outbox / 业务库事务**：dsh-java **主线是 Harness 运行时**，工具副作用多落在 shell/fs/MCP/插件侧；**没有**课仓 A9/B1 那种「Signal → Outbox → Java 领域 API 幂等建单」完整链。面试应说：课仓证明归属与幂等设计，dsh-java 证明 Java 侧 Harness/事件/审批工程化；**不要**声称本仓库已上 Temporal 或已有采购单 Outbox。

**挂科现场**：把 Session Event Log 说成「就是 Outbox」；或说「审批通过 = 副作用已提交」；或把 LLMentor 课内循环说成生产归属链。

**证据锚点**

- `.../agent/service/run/ReactLoopAgent.java`
- `.../tool/service/ToolCallExecutor.java`
- `.../tool/service/MatrixRuntimeApprovalGate.java`
- `.../session/event/service/SessionEventLogService.java`
- `.../session/event/model/valobj/SessionEventType.java`
- 课仓对照：`03-modules/A9-capstone/`、`04-frontier/B1-durable-runtime/OWNERSHIP.md`

#### 评分

（待 agent学生作答后回填）

---

### O9 · 运行期审批（Java高级架构师）

#### 面试官提问（Java高级架构师）

> 场景：会话里模型要调一个矩阵里标记「需审批」的 `shell_*` / `plugin__*` 工具。
> 1. `MatrixRuntimeApprovalGate.check` 在什么条件下 ALLOW / DENY / 进入 ask？`FULL_OPEN`、`AUTO_APPROVE`、`allowForSession` 各意味着什么生产风险？
> 2. ask 路径如何挂起：`RuntimeApprovalBroker.requestApproval` 与 REST `resolve` 如何唤醒？超时默认什么裁决？
> 3. 与「任务审批」API（`IHarnessApproval*` / task 上下文）如何分工？面试官若问「审批是不是 Flowable」，你怎么用本仓库事实回答？
> 4. DENY 时为何必须仍由 `ToolCallExecutor` 写出成对失败 `tool_result`？（可引用 Q2）
>
> 带类名；讲不清「默认放行 / askHandler 空」直接痛点不及格。

#### 候选人解答（agent学生）

（待答）

#### 面试官标准答（Java高级架构师 · 金标）

1. **Gate 语义（`MatrixRuntimeApprovalGate`）**
   - 不在 `approvalRequiredTools` → ALLOW  
   - 已 `allowForSession(tool)` → ALLOW（会话级放行）  
   - `ApprovalModeVO.FULL_OPEN` → 全放行（**生产高危开关**）  
   - 需审批且 `AUTO_APPROVE` → ALLOW（自动化场景，需审计）  
   - 否则走 `askHandler`；**askHandler == null → DENY**（防御默认，优于静默放行）
2. **Broker 挂起（`RuntimeApprovalBroker` implements `RuntimeApprovalGateway`）**
   - `requestApproval`：登记 pending + `CompletableFuture.get(timeout)` 阻塞 agent 线程  
   - 前端/API `listPending` + `resolve(approvalId, verdict)` 完成 future  
   - 分支对齐：allow-once / allow-session / deny / cancel；**超时 → DENY**（默认 10min）  
   - 六边形：trigger 依赖 `RuntimeApprovalGateway` 端口，不直耦 Broker 实现
3. **两类审批**
   - **运行期工具审批**：拦在 `ToolCallExecutor` 路径上，保护 shell/插件等即时副作用  
   - **任务审批**（`IHarnessApproval*` / task 聚合）：任务生命周期态机，不等于工具 Gate  
   - 本仓库 **不是** Flowable/BPMN 中心；企业 EHS 里的 `geek-flow` 是另一套。面试应说「Harness 内建运行期 Gate + Broker」，不要冒充流程引擎全家桶。
4. **DENY 与事件成对**：Q2 已证——仍 `appendToolCall` + 合成失败 `tool_result`（`APPROVAL_REQUIRED`），否则 `SessionRebuilderService` 重建会悬挂。

**痛点**：矩阵漏配 + FULL_OPEN；askHandler 未注入却以为「会弹窗」；把超时当 ALLOW；任务审批通过误当成工具已执行。

**证据锚点**

- `MatrixRuntimeApprovalGate.java`、`RuntimeApprovalBroker.java`、`RuntimeApprovalGateway.java`
- `IRuntimeApprovalApi` / `ResolveRuntimeApproval*` DTO
- case：`cases/approval/RuntimeApprovalCaseImpl.java`

#### 评分

（待答后回填）

---

### O10 · 事件溯源事故七段（Java高级架构师）

#### 面试官提问（Java高级架构师）

> 事故：运维在 turn 中途 unload 插件 / 或审批 DENY 后，控制台回放缺 `tool_result`，会话重建相位错乱。按七段口述（墙钟目标约 2 分钟，②⑦不可砍）：
> 1. 场景与影响  
> 2. **Ownership**（谁该保证成对事件 / 写租约）  
> 3. Trace/事件卡点（点 `SessionEventType`）  
> 4. 根因  
> 5. 修复  
> 6. 回归门禁  
> 7. **指标关闭**  
>
> 必须落到 `SessionEventLogService` / `SessionWriteLeaseService` / `SessionRebuilderService`；禁止只说「加个日志」。

#### 候选人解答（agent学生）

（待答）

#### 面试官标准答（Java高级架构师 · 金标）

**七段金标（可压缩，②⑦不砍）**

1. **场景**：插件热更新失败紧急 unload，或高危工具 DENY；客诉「回放缺结果 / 重建后 Agent 相位不对」。  
2. **Ownership（不可砍）**：`ToolCallExecutor` 拥有成对 `TOOL_CALL`/`TOOL_RESULT`；`SessionEventLogService`（经 `SessionWriteLeaseService`）拥有追加顺序与租约；`SessionRebuilderService` 只投影、不补写真相。Unload/cancel 的运维归属是「先 `Agent.cancel` 再 unload」（Q3）。  
3. **卡点**：事件流见 `TOOL_CALL` 后无匹配 `TOOL_RESULT`；或写租约冲突（`SessionWriteLeaseConflictException`）导致部分写入失败。  
4. **根因**：把「注册表消失 / 审批拒绝 / 杀线程」当成可以不闭合事件；或并发写同一 session 无租约。  
5. **修复**：DENY/HOOK_BLOCKED/ABORTED/registry-miss **一律合成失败 result**；unload runbook 强制先 cancel；追加走 `withWriteLease`。  
6. **回归**：负例——DENY 成对、cancel 中途成对、双写租约冲突可观测；CI 卡「悬挂 tool_call」。  
7. **指标关闭（不可砍）**：悬挂 `tool_call` 数 → 0；重建后相位错误工单 7 日归零；unload 未先 cancel 的变更评审 = 0。

**与课仓对齐一句话**：A6/A9 的 Trace→fixture 是评测门禁；dsh-java 的 Session Event Log 是**运行时真相源**——两者都要求「失败也要成对可回放」。

**证据锚点**

- `SessionEventLogService.append` / `SessionWriteLeaseService`
- `SessionRebuilderService.rebuild`
- `SessionEventType.TOOL_CALL` / `TOOL_RESULT`
- `PersistingSessionLog`（若 run 路径经此落库）

#### 评分

（待答后回填）


## 本场纪律



1. 证据只承认：本机路径、本仓库 `projects/hotplug-harness`、已合 PR 文档。  
2. 课程工程（LLMentor）与 Harness（dsh-java）**角色不同**，混为一谈直接扣「架构归属」分。  
3. 出题人标准答与候选人答并列入库；打分后改状态表。

## 状态

- Q1：已完成（8.5）  
- Q2：已完成（8.8）  
- Q3：已完成（9.0）；深挖三题均过关  
- G1 / O9 / O10：题面 + 金标已由 Java高级架构师写入；**待 agent学生作答**，答后架构侧评分回填  
