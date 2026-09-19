# Mock Interview Round 5 · 架构续面（写租约 / 两类审批）· 2026-09-19

## 元信息

| 项 | 内容 |
|----|------|
| 候选人 | agent学生 |
| 出题 / 评分 | Java高级架构师（本场架构段） |
| 前置 | R4 整场完成；复盘见 [round-04-review-and-next.md](round-04-review-and-next.md) |
| 证据主仓 | `E:\deepseek-harness-java` |
| 硬约束 | 题面 + **金标答** + 候选人答 + 评分全文入库；查真实痛点，不编造 |

## 议程

| # | 题 | 状态 |
|---|----|------|
| R5-C | 写租约冲突：双实例写同一 session | **已答 / 已评分 9.3** |
| R5-D | 任务审批 vs 运行期工具审批联调故事 | **已答 / 已评分 9.3** |

> R5-A/B（LLMentor 对比 / 缺 TOOL_RESULT 排障）由 Agent工程师出题；R5-E 限时连考双方联合。

---

### R5-C · 写租约冲突（双写同一 session）

#### 面试官提问（Java高级架构师）

> 场景：两台实例（或两个线程）同时对同一 `sessionId` 追加 Session Event——例如用户双开标签、重试未取消旧流、或故障转移后旧实例未释放租约。
> 1. `SessionWriteLeaseService` 的 `acquire` / `renew` / `requireWritable` / `release` 各解决什么？未持有合法租约时写会发生什么（点异常类）？
> 2. `SessionEventLogService.append` 如何与租约配合？若旧实例租约未过期，新实例抢写会怎样？TTL 过期后谁能接手？
> 3. 生产上：冲突是「静默丢事件」还是「显式失败」？前端/运维应看到什么？如何避免「双 SSE 同时 kick」？
> 4. 对照课仓 A8/A9：lease 概念是否相同？一句话划清「会话写租约」vs「Worker 执行租约」。
>
> 必须带本机类名；说「加锁就行」无机制不及格。

#### 候选人解答（agent学生）

**1) `SessionWriteLeaseService` API**

- `acquire(sessionId, owner, ttl)`：`putIfAbsent`；已有**未过期**租约 → 抛 `SessionWriteLeaseConflictException`；仅当旧租约**已过期**才 `replace` 接手。
- `renew`：必须同一 `leaseId` 且未过期，否则 conflict。
- `requireWritable`：先清过期租约；若仍存在其它 `leaseId` → conflict。
- `release`：仅 `leaseId` 匹配才摘掉。

**2) 与 EventLog 配合**

`SessionEventLogService` 的 `createSession` / `append` / `appendBatch` 经 `withWriteLease`（acquire，TTL 约 30s → 写 store → `finally release`）。旧实例租约未过期时，新实例 **acquire 失败**，不能并行追加；TTL 到期后另一实例可 acquire 接手（故障转移窗口）。

**3) 生产可见性**

- 冲突必须是**显式失败**，不能静默丢事件。
- 监控 `SessionWriteLeaseConflictException` 计数；前端/运维应看到写失败语义。
- 防双写：同一会话先 `cancel` 旧 SSE/驱动再开新流，或网关层会话互斥；禁止未 cancel 的双 kick。

**4) 与课仓对照**

A8/A9 Worker lease = **任务执行权 / 防双 Worker**；此处 = **Session Event 追加单写者**。概念都是 lease，对象不同，面试勿混称。


#### 面试官标准答（Java高级架构师 · 金标）

**目标**：同一 session 的事件追加必须**单写者**；冲突要失败可见，不能默默交叉写坏回放。

1. **API 语义（`SessionWriteLeaseService`）**
   - `acquire(sessionId, owner, ttl)`：`putIfAbsent`；若已有未过期租约 → 抛 `SessionWriteLeaseConflictException`；仅当旧租约**已过期**才 `replace` 接手。
   - `renew`：必须持有同一 `leaseId` 且未过期，否则 conflict。
   - `requireWritable`：存在其它未过期 `leaseId` → conflict；过期则清理后允许（调用方仍应持有自己的 lease 上下文）。
   - `release`：仅当 `leaseId` 匹配才摘掉。
2. **与 EventLog 配合**：`SessionEventLogService` 在 `createSession`/`append`/`appendBatch` 等路径经 `withWriteLease`——先拿到租约再 `store.append`。旧实例租约未过期时，新实例 **acquire 失败**，不能并行追加。TTL 到期后另一实例可 acquire 接手（故障转移窗口）。
3. **生产可见性**
   - 正确行为：**显式失败**（conflict 异常上浮），而不是吞掉事件。
   - 运维/前端：应看到写失败/409 类语义或错误事件；监控 `SessionWriteLeaseConflictException` 计数。
   - 防双写：同一会话同时只允许一条活跃 Agent 驱动（取消旧流再开新流；网关层会话互斥；禁止未 cancel 的双 SSE kick）。
4. **与课仓对照**：A8/A9 的 Worker lease 管的是**任务执行权/防双 Worker**；此处是 **Session Event 追加单写者**。概念都是 lease，对象不同——面试勿混称。

**痛点**：进程崩溃不 release → 等 TTL；TTL 过短 → 正常 turn 中 renew 失败；双标签同时 stream → 冲突风暴；把 conflict 吃掉 → 回放丢步。

**证据**

- `.../session/event/service/SessionWriteLeaseService.java`
- `.../session/event/service/SessionWriteLeaseConflictException.java`
- `.../session/event/service/SessionEventLogService.java`（`withWriteLease`）

#### 评分

| 维度 | 分 | 评语 |
|------|----|------|
| API 语义 | 9.5/10 | acquire/renew/requireWritable/release 与过期 replace 说清 |
| EventLog 耦合 | 9.5/10 | `withWriteLease`、TTL、接手窗口正确 |
| 生产可见性 | 9/10 | 显式失败 + 监控 + 防双 SSE；可再补「conflict 吃掉→回放丢步」痛点句 |
| 课仓对照 | 9.5/10 | Worker lease vs Session 写租约边界清楚 |
| **总分** | **9.3/10** | 写租约题过关偏强 |

**缺口**：可补一句「进程崩溃不 release → 等 TTL」运维窗口。


---

### R5-D · 任务审批 vs 运行期工具审批联调

#### 面试官提问（Java高级架构师）

> 讲一个联调故事（可假设）：用户提交高危画像任务，策略要求人工批；批准入队执行后，ReAct 循环里又要调矩阵内的 `shell_*`。
> 1. **任务审批**路径：从哪到哪？（点 `IApprovalPolicyService.decide`、`ApprovalCommandService.approve`、会话状态 `PENDING_APPROVAL` → `QUEUED`、以及是否记 session log）
> 2. **运行期工具审批**路径：为何任务已批准，工具仍可能再拦？（`MatrixRuntimeApprovalGate` + `RuntimeApprovalBroker`）
> 3. 两套审批**状态机是否共用**？混用会出什么事故（例如：任务批准误当成 shell 已授权；或工具 DENY 却把任务标完成）？
> 4. 若面试官问「能不能统一成 Flowable 一个流程？」你怎么用本仓库边界回答（诚实，不贬低也不硬吹）？
>
> 带类名；画不清两条链直接不及格。

#### 候选人解答（agent学生）

**1) 任务审批链**

- 策略：`IApprovalPolicyService.decide(profileCode, permissionAssessment)`（策略来自 `IApprovalPolicyPort` / `ApprovalPolicyVO.approvalRequiredProfiles`）
- 挂起：会话 `HarnessStatusEnumVO.PENDING_APPROVAL`
- 放行：`ApprovalCommandService.approve(sessionId)` 校验状态 → `QUEUED` → `sessionLogService.recordApprovalAccepted` → `harnessExecutionService.executeSession`
- API：`IHarnessApproval*`（与运行期 `IRuntimeApprovalApi` 分立）

**2) 运行期工具审批链**

发生在 `ToolCallExecutor` 内：`MatrixRuntimeApprovalGate.check`；需 ask 时 `RuntimeApprovalBroker.requestApproval` 阻塞，REST `resolve` 唤醒。  
**任务已 QUEUED/执行中 ≠** 某条 `shell_*` 已 `allowForSession`。

**3) 状态机不共用**

任务态（PENDING_APPROVAL / QUEUED / …）≠ Broker pending map 的 `approvalId`。  
混用事故：任务批过后跳过工具 Gate → shell 裸奔；工具 DENY 却标任务完成 → 假成功；把流程引擎节点 ID 当成 Broker approvalId → 串台。

**4) 能否统一 Flowable？**

企业单据流适合 Flowable/`geek-flow`；dsh-java 价值是 Harness 内工具级挂起（Gate + Broker）。可演进为「任务级流程引擎 + 工具级仍 Gate」，但**本仓库未收成单一 BPMN**——面试诚实分层，不硬吹已全上 Flowable。


#### 面试官标准答（Java高级架构师 · 金标）

**目标**：两条链目的不同——**任务能不能开跑** vs **这一下工具能不能动外部环境**。

1. **任务审批链（会话/任务生命周期）**
   - 策略：`IApprovalPolicyService.decide(profileCode, permissionAssessment)`，策略来自 `IApprovalPolicyPort` → `ApprovalPolicyVO.approvalRequiredProfiles`
   - 挂起：会话处于 `HarnessStatusEnumVO.PENDING_APPROVAL`
   - 放行：`ApprovalCommandService.approve(sessionId)` 校验状态 → `QUEUED` → `sessionLogService.recordApprovalAccepted` → `harnessExecutionService.executeSession`
   - API 面：`IHarnessApproval*` / task 审批用例（与运行期 `IRuntimeApprovalApi` 分立）
2. **运行期工具审批链（工具副作用门禁）**
   - 发生在 `ToolCallExecutor` 内：`MatrixRuntimeApprovalGate.check`；需 ask 时 `RuntimeApprovalBroker.requestApproval` 阻塞；REST resolve 唤醒
   - **任务已 QUEUED/执行中，不自动等于** 某条 `shell_*` 已 allow-session
3. **不可混用**
   - 状态机：**不共用**。任务态（PENDING_APPROVAL/QUEUED/…）≠ Broker pending map 里的 approvalId
   - 事故：任务批过后跳过工具 Gate → shell 裸奔；工具 DENY 却把任务标 COMPLETED → 业务假成功；把 Flowable/geek-flow 节点 ID 当成 Broker approvalId
4. **统一 Flowable？**  
   - 企业单据流（EHS 维保计划等）适合 `geek-flow`/Flowable；  
   - dsh-java 的价值是 **Harness 内毫秒～分钟级工具挂起**（Broker Future）+ 权限矩阵；  
   - 可演进为「任务级走流程引擎、工具级仍走 Gate」，但**本仓库尚未把它收成单一 BPMN**——面试应诚实说分层，而不是「我们已经全上 Flowable」。

**痛点**：产品把「批任务」按钮复用成「批工具」；AUTO_APPROVE/FULL_OPEN 让第二道门形同虚设；超时 DENY 未闭合 tool_result（R4 Q2/O10）。

**证据**

- `ApprovalCommandService.java`、`IApprovalPolicyService.java`、`ApprovalPolicyVO`
- `MatrixRuntimeApprovalGate.java`、`RuntimeApprovalBroker.java`、`RuntimeApprovalGateway.java`
- `IHarnessApproval*` vs `IRuntimeApprovalApi`

#### 评分

| 维度 | 分 | 评语 |
|------|----|------|
| 任务链 | 9.5/10 | decide → PENDING → approve → QUEUED → record → execute 完整 |
| 工具链 | 9.5/10 | Gate + Broker；任务批≠工具放行 |
| 混用事故 | 9.5/10 | 裸奔 / 假完成 / ID 串台三点齐 |
| Flowable 边界 | 9/10 | 诚实分层；可再点「毫秒～分钟工具挂起」为何不宜整段 BPMN |
| **总分** | **9.3/10** | 联调故事过关偏强 |

**缺口**：点名 `FULL_OPEN`/`AUTO_APPROVE` 会让第二道门失效（接 R4 O9 漏句）。


---

## 本场纪律

1. 先答 R5-C 再答 R5-D；每题对照金标补「漏句」。  
2. 证据只承认本机路径与已合 GitHub 文档。  
3. 与 Agent工程师的 R5-A/B 可并行，但不要抢改同一 markdown 冲突区。

## 状态

- R5-C：已完成（9.3）  
- R5-D：已完成（9.3）  
- R5 架构段收束  
