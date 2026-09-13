# 简历三条差异化（投递用）

> 面向：3–5 年 Agent 应用 / Agent 后端岗。  
> 原则：**不写框架清单**；每条 = 场景 + 做法 + 证据路径 + 可追问指标。  
> 配套模拟面：`docs/mock-interviews/round-0{1,2,3}-*.md` · 课纲：`curriculum/advanced/**`

**一句话定位（可放简历摘要）**  
四年 Java 背景转向 Agent 平台：能把 **网关抬权 → 编排续跑 → 领域事务** 拆清，并用故障注入 + Eval 门禁证明「不双写、不串租、不靠 Prompt 当安全边界」。

---

## 差异化 ① · Java 归属链（不是纯 Python Demo）

**简历条目（中文，约 2–3 行）**

> 设计多租户企业 Agent 控制面身份与事务边界：Spring 网关签发短时内部令牌（aud/TTL），Python Harness/Temporal 只信内部令牌并注入四隔离键；HITL/Signal 后经 Outbox/Activity 调用 Java 领域 API 落本地事务与幂等，禁止 Workflow/Signal 内直接打款或持业务库超管账号。

**英文短版（可选）**

> Owned identity/transaction boundaries for a multi-tenant agent control plane: short-lived internal tokens from a Java gateway; orchestration (Harness/Temporal) never runs business DB tx; approved side effects go Outbox/Activity → idempotent domain API.

**面试官一追问你就接**

| 追问 | 你答的钩子 | 仓库证据 |
|------|------------|----------|
| 为何不信用户 JWT？ | aud 绑定、短 TTL、日志拖库风险；HITL 跨天要续签 | A3/A9 identity · R3 题 2.1 |
| Signal 里能不能 UPDATE？ | 不能；重复 Signal / 崩溃双写 | B1 OWNERSHIP · R3 2.2 |
| 谁开事务？ | 只在 Java 领域服务 | `docs/b1-durable-runtime-research.md` §2 |

**不要写成**：`熟悉 Spring / Temporal / Python`（无边界）。

---

## 差异化 ② · 坏例回放进 CI（不是「有个 Judge」）

**简历条目**

> 搭建四层 Eval（Model/Framework/Harness/Application）与硬门禁：危险工具误开、缺 retrieve.filter、holdout 回退 ≥2pt 一票否决；线上/注入 Trace 经 PII 脱敏落入 regression，incomplete fixture 禁止写入 holdout，保证坏例下一轮 CI 必跑。

**英文短版**

> Shipped four-layer eval with hard release gates; trace-to-fixture (PII-stripped) feeds regression CI; incomplete traces (e.g. missing retrieve.filter) cannot enter holdout.

**面试官一追问你就接**

| 追问 | 钩子 | 证据 |
|------|------|------|
| 线下 +3% 能发吗？ | 软分不覆盖硬门禁 | A6 · O8 · R2 Q12 |
| 坏例怎么进回归？ | Trace→fixture→CI | A9 (e) · A6 `trace_to_fixture` |
| 两套「四层」？ | 先声明课纲口径再映射结果/轨迹/成本/对抗 | R2 Q12 |

**不要写成**：`使用 Langfuse/DeepEval 做评测`（无红线、无闭环）。

---

## 差异化 ③ · MCP ≠ A2A（不是「接了 MCP」）

**简历条目**

> 区分工具协议与 Agent 委托：MCP 侧用 Registry 钉版本 + schema 指纹 + 描述防投毒 + 沙箱；跨 Agent 委托走 A2A，强制下行身份、任务级幂等键与 deadline/取消，超时取消后副作用次数为 0，避免与 `call_tool` 混用导致孤儿任务。

**英文短版**

> Separated MCP tooling (pinned schema fingerprint, anti-poisoning, sandbox) from A2A delegation (downstream identity, idempotency key, deadline/cancel with zero side effects after cancel).

**面试官一追问你就接**

| 追问 | 钩子 | 证据 |
|------|------|------|
| description 被改怎么办？ | MCP 非安全边界；比对 Registry | A5 · O5 |
| 叫另一个 Agent 走 MCP？ | 挂；走 A2A | B2 `DESIGN.md` |
| 取消后？ | status=cancelled 且 side_effect_count=0 | B2 demo4/5 |

**不要写成**：`熟悉 MCP/A2A 协议`（无负例）。

---

## 作品集主链接（简历「项目」栏）

| 项目名建议 | 一句话 | 路径 |
|------------|--------|------|
| 多租户企业 Agent 控制面（Capstone） | 五段演示：四键 / 幂等 Outbox / RAG ACL / 熔断 / Trace→Eval | `curriculum/advanced/A9-capstone/` |
| Durable Runtime 对照（Temporal） | Signal→Activity 幂等；超管 DB bypass 挂科 | `curriculum/advanced/B1-durable-runtime/` |
| 最小 A2A | 身份·幂等·超时取消 | `curriculum/advanced/B2-a2a/` |

模拟面记录（可放「面试准备」或内推附录，一般不放对外简历正文）：  
`docs/mock-interviews/`（R1–R3 已通过）。

---

## 投递前自检（打勾）

- [ ] 三条都落到具体仓库路径，能脱稿 90s/条
- [ ] 摘要里出现「Java 网关 / 领域事务 / 门禁」至少各一次
- [ ] 全文搜索简历：删掉纯名词堆叠（LangGraph/MCP/RAG 并列无动词）
- [ ] O10 七段脱稿计时 ≤ 2min（R3）
- [x] @Java高级架构师 审过①归属链表述；[ ] @Agent工程师 审过②③

## 审稿栏（请直接改本文件）

| 审阅人 | 结论 | 修改意见 |
|--------|------|----------|
| Java高级架构师 | **通过** | ①表述准确：抬权/aud/TTL、四键、Outbox→领域事务、三项挂科都在。非阻塞：条目里可加「mTLS/内网只收网关」半句（R3 图已有），字数紧可省略。 |
| Agent工程师 | （待填） | |
