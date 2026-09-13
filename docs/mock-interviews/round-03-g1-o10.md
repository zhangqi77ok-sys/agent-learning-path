# Mock Interview Round 3 · 2026-09-13

## 元信息

| 项 | 内容 |
|----|------|
| 候选人 | agent学生 |
| 架构面试官 | Java高级架构师（G1 + 身份/事务追问） |
| 深挖面试官 | Agent工程师（O10 七段全长） |
| 形式 | 书面模拟全文入库；建议另做 15min 限时口述 |
| 证据库 | https://github.com/zhangqi77ok-sys/agent-learning-path |
| 前置 | R1/R2 已通过；O10 附录 A/B 已合；`docs/deep-dive-must-ask.md` |

## 议程

| # | 题 | 侧 | 口径 |
|---|----|----|------|
| 1 | G1 企业知识助手端到端（图+SPOF+SLO+身份链） | 架构 | 15–20 min |
| 2 | 架构三连追问（令牌 / Outbox / ACL 顺序） | 架构 | 8 min |
| 3 | O10 七段全长（对照附录 A） | 深挖 | 12–15 min |
| — | 假 Trace 排障（可选加时） | 深挖 | 5 min |

---

## 题 1 · G1 白板：企业知识助手端到端

### 面试官提问（Java高级架构师）

> 画「企业知识助手」端到端。必须出现：Java 网关、Harness/Runtime、模型网关、PG（checkpoint/ledger）、检索、Registry/沙箱、Outbox、OTEL、Eval。标 **至少 2 个 SPOF** 和 **2 个数字 SLO**。身份从哪进、副作用从哪出。

### 候选人解答

#### 1.1 组件图（口述/白板文字版）

```
[Browser/App]
    │ 用户登录
    ▼
[Spring Gateway] ──签发短时内部令牌──► (tenant,user,roles,aud,exp)
    │ 命令（可选 MQ：StartRun/Cancel）
    ▼
[API / Control Plane] 创建 thread/run，注入四键（不可被模型改）
    │
    ├─► [Harness] Loop/预算/熔断/Replay ──► [Model Gateway] 路由/429/预算
    │         │                                    │
    │         ├─ retrieve（ACL 前过滤）──► [Index/PG 向量或词法]
    │         ├─ tools via [Registry+沙箱]（MCP 钉版本/指纹）
    │         └─ HITL ──► 审批服务 ──► [Outbox] ──► [Java 领域 API]（本地事务+幂等）
    │
    ├─► [Runtime Workers] 队列+租约（或 Temporal Worker）
    ├─► [PG] checkpoint / effect_ledger / outbox / audit
    └─► [OTEL] ──► Trace→fixture ──► [Eval 门禁/holdout] ──► 发版/金丝雀
```

**归属一句话（简历差异化）**  
Java 网关抬权 → MQ/API 命令 → Temporal/Agent 编排 → **领域事务只在 Java**。

#### 1.2 SPOF（至少点名 + 缓解）

| SPOF | 为什么危险 | 缓解 |
|------|------------|------|
| 单区 / 单机 Postgres | checkpoint+ledger 全挂，无法续跑与审计 | 托管多 AZ；RPO/RTO 讲清；私有化单机必须写进风险 |
| 单模型供应商 | 429/5xx 雪崩 | A7 fallback + 熔断；15s 内明确终态 |
| 单审批队列无持久化 | HITL 丢失 / 双投 | 持久化审批 + 幂等 resume |
| Registry 单点且无钉版本缓存 | 工具全不可用或被投毒 | 钉版本本地副本；变更评审 fail-closed（A5） |

#### 1.3 SLO（课程建议值，面试要说「我们门禁/演示用的数」）

| SLO | 值 | 证据 |
|-----|-----|------|
| 跨租户越权（检索+工具） | **= 0** | A4/A9-c 注入 |
| 已批准副作用 / 幂等键 | **= 1** | A9-b / B1 |
| 只读问答 P95 | **< 8s**（声明环境） | A9 README |
| holdout 回退 | **≥2pt 阻断发版** | A6 |
| 吵闹租户下邻居 P95 | **≤ 2× 基线** | A8 |

#### 1.4 身份进、副作用出

- **进**：只信 Gateway 内部令牌；Agent 不验用户密码、不把用户 JWT 当权威（G7）。
- **出**：高风险必须审批 → Outbox/Activity → Java 领域 API；禁止 Signal/Workflow 内直接打款。

**证据路径**：A8 `DEPLOY.md` · A9 · B1 `OWNERSHIP.md` · `docs/b1-durable-runtime-research.md`

---

## 题 2 · 架构三连追问（本场必答）

### 2.1 内部令牌 vs 用户 JWT（aud / TTL / 续签）

**问**：为什么 Agent 不能直接信用户 JWT？审批跨天怎么办？

**答**：

| | 用户 JWT | 内部令牌 |
|--|----------|----------|
| 签发 | IdP / 登录 | Spring 网关抬权后 |
| aud | 面向 BFF/多服务 | **绑死** `python-agent` / `a2a-server` |
| TTL | 往往较长 | **短**（分钟级），降低日志拖库风险 |
| 刷新 | 用户会话 | HITL 长等待：**续签/重新抬权**，校验时钟偏差；过期审批直接 `approval_expired` |

伪造 tenant claim → HMAC 失败；错 aud / 过期 → 拒。  
**证据**：A3/A9 identity · R1 G7 · follow-up：续签细节可再补 PASS。

### 2.2 Signal/HITL 后为何必须 Outbox 再进 Java 事务

**问**：批准 Signal 里直接 `UPDATE balance` 行不行？

**答**：不行。Signal 可重复、Worker 可在 Signal 后崩溃。正确：Signal 只记意图 → ledger/Outbox → **Activity 调 Java 领域 API（本地事务 + 幂等键）**。  
Temporal Workflow **不是**业务事务。  
**证据**：B1 demo · O9 · 死亡坑 1/3。

### 2.3 多租户下：网关与检索 ACL 谁先拦

**问**：网关过了是否还要检索 ACL？顺序？

**答**：

1. **网关先**：无令牌 / 错 aud / 过期 → 请求进不来。
2. **控制面**：四键写入，拒绝客户端传 tenant。
3. **检索仍要 ACL**：网关解决「你是谁」；检索解决「这份文档你能不能看」（角色、过期、版本）。**评分前过滤**，防 Prompt 越权与 Trace 泄漏。
4. 工具层再 ACL/沙箱（A5）。

**证据**：A3 + A4 + Capstone (c)。

---

## 题 3 · O10 七段全长（对照附录 A）

### 面试官提问（Agent工程师）

> 用作品集讲一次等价生产事故。必须七段齐全，不许只说框架名。对照 R1 附录 A 的 ownership 与指标。

### 候选人解答（七段）

#### ① 用户场景与影响面

多租户采购/报销助手：经理在 HITL 批准「创建采购单」后，用户连点「继续」，或审批重放 / Worker 重启。外部采购系统出现 **两张语义相同单据**，财务对账混乱，客诉 `dup_ticket`。

#### ② Ownership（你负责哪一段）

| 段 | Owner |
|----|-------|
| 幂等键规范、ledger/outbox、重复 resume/Signal 外壳、发布硬门禁 | **我（Agent Runtime/平台）** — A2/A9/B1 |
| 工单本地事务、按 key 去重、拒绝无 key 写入 | **Java 领域服务** |
| 审批人配置、发现双单后按 key 合并 | **业务 Oncall** |

不是「上了 Temporal 就没人负责」。

#### ③ Trace 上卡在哪

- span：`signal.approval_granted` 出现两次或 `workflow.resume` 两次。
- `effect_ledger`：同一 `idempotency_key` 若设计错误会看到两次 `started` 或两次外部 `POST`。
- 健康设计下：第二次应命中 `external_ref` 已存在 / 上游 find 命中，**不应**再 `create`。

#### ④ 根因（机制）

把「审批通过」当成可重复副作用；**checkpoint/Signal 恢复的是编排意图，不是外部世界**。缺稳定 `tenant:thread:effect` 幂等与 Outbox 收敛时，至少一次投递变成双单。

#### ⑤ 修复

1. 幂等键稳定化；调外部前 find-or-create。  
2. Signal/HITL → Outbox/Activity → Java API。  
3. 重复 resume / 重复 Signal 回归用例。  
4. OWNERSHIP 挂科清单：禁 Signal 打款、禁 Workflow 事务、禁 Worker 超管库。

#### ⑥ 回归 / 门禁如何防再发

- CI：A9-b、B1 demo2（`create_calls==1`）必绿。  
- 硬门禁：危险工具 / 缺 filter 等（A6）；缺幂等键的高风险路径评审拒绝。  
- Trace→fixture：双写类坏例进 regression（A9-e）。

#### ⑦ 事后指标变化（关闭条件）

| 指标 | 事故时 | 目标 |
|------|--------|------|
| 外部建单数 / 幂等键 | >1 | =1 |
| 重复 resume CI | 无/红 | 每 PR 绿 |
| `dup_ticket` 客诉 7 日 | >0 | =0 |
| Signal 直写业务库 | 可能 | 评审 =0 |

连续两迭代达标 + CI 绿 → 事故从「缓解」标「关闭」。

**证据**：R1 O10 + 附录 A/B · A2 · A9-b · B1 RUN · `HOLES.md` #1/#3

### 90 秒压缩版（计时演练用）

同 R1 附录 B；本场要求能不看稿展开到七段。

---

## 可选加时 · 假 Trace 排障

**给候选人一段（书面）**：

```json
{
  "spans": [
    {"name": "tool.retrieve", "attributes": {}},
    {"name": "harness.step", "attributes": {"tools": ["retrieve", "export_all"]}}
  ],
  "answer": "已导出全部客户"
}
```

**期望定位**：Application 缺 `retrieve.filter`（incomplete）+ Harness/策略层危险工具误开 → **硬门禁否决发版**，不是先换模型。

---

## 出题人评分（待填）

| 题 | 分数 (1–5) | 是否过关 | 补洞 |
|----|------------|----------|------|
| G1 图+SPOF+SLO | 5 | 过 | 无；组件齐全，归属链与简历差异化一句到位 |
| 三连追问（令牌/Outbox/ACL） | 5 | 过 | 非阻塞：HITL 续签细节可再写进 PASS（已点名 follow-up） |
| O10 七段 | 5 | 过 | 无；七段对照附录 A 齐全，ownership/指标关单条件到位 |
| 假 Trace（若考） | — | 未考 | 期望定位已写进题干，合入后做脱稿排障演练即可 |

**整场结论**：**深挖侧 O10 七段过关**；**架构侧 G1 + 三连追问过关**。Mock R3 通过。

**深挖评语（Agent工程师）**：七段不再偏「只讲机制」——ownership 三分表、Trace 卡点、根因（编排意图≠外部世界）、修复、CI/坏例回放、指标关单条件一条龙。和 R1 附录 A 对齐，达到 3–5 年岗事故题过线标准。假 Trace 题干期望定位正确，建议合入后计时演练。

**架构师评语（Java高级架构师）**：白板把「身份进 / 副作用出」画死了；SPOF 带缓解、SLO 可测。三连追问覆盖 aud/TTL/续签、Signal→Outbox→Java、网关与检索 ACL 分层，是 3–5 年转岗可过线答法。

**建议补洞**：

- [x] 深挖侧评分已填
- [ ] 限时 15min 口述录音/纪要另开 `round-03-timed.md`（可选）

---

## 候选人自检

- [x] G1 图画全且有归属链
- [x] SPOF≥2、SLO≥2
- [x] 三连追问写清
- [x] O10 七段对照附录 A
- [ ] 脱稿 15min 计时（合入后做）
