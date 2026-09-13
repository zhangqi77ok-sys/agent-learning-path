# 深挖面试官 · 必追问清单（Agent工程师）

> 用途：3–5 年 Agent 应用/后端岗模拟面与投前自检。  
> 约定：答「用了 LangGraph / Temporal / MCP」而不讲失败与边界 = **直接打回**。  
> 配套：[interview-deep-dive-v2.md](interview-deep-dive-v2.md) · Mock R1/R2 · Capstone A9

## 过关总口径

每题必须能讲清三截：

1. **失败现场**（谁在什么状态下挂了）
2. **修法**（哪一层拦、哪个键、哪个状态机）
3. **防回归**（Trace 字段 / 评测用例 / CI 门禁）

---

## A. 一票否决（不过别投）

| ID | 追问 | 挂科句 | 证据锚点 |
|----|------|--------|----------|
| O1 | 工具已 200，ledger 仍 `started` 无 ref，resume 怎么办？ | 「再调一次」 | A2 demo1a · A9-b · B1 |
| O4 | 多租户同索引，过滤在哪一层？为何不能 Prompt？ | 「先检索再让模型丢掉」 | A4 · A9-c |
| O5 | MCP description 被改成导出全库？ | 「协议是安全的」 | A5 · HOLES#5 |
| O8 | 线下 +3% 今晚发？ | 「分高就发」 | A6 · A9-e |
| O10 | 结构化事故（七段） | 只有机制无 ownership/指标 | R1 附录 A/B |

## B. 场上高频追问（深挖侧）

| ID | 追问 | 及格要点 |
|----|------|----------|
| Q1 | Model / Harness / Runtime？LangGraph 哪层？ | Runtime≠LangGraph；预算/熔断在 Harness |
| Q2 | 四键；伪造 `tenant_id` 哪层拒？ | tenant 只来自内部令牌 |
| Q11 | 死循环怎么停？ | 多维预算 + 重复 signature circuit |
| Q12 | 四层 Eval；「答得不好」先查哪？ | 先 Trace 映射层；两套四层能对照 |
| MCP≠A2A | 委托兄弟 Agent 能否 `call_tool`？ | A2A 要身份/幂等/deadline/取消（B2） |
| 坏例闭环 | 线上越权一次如何进 CI？ | Trace→脱敏 fixture→regression；incomplete 禁 holdout |

## C. 限时演练建议

1. **90s**：O10 全长（附录 B）计时背，不许看稿。
2. **3min 白板**：画 Model/Harness/Runtime，标预算与租约落点。
3. **假 Trace 排障**：给缺 `retrieve.filter` 或双 Signal 的 span，说出先怀疑哪一层、加哪条门禁。

## D. 简历差异化（深挖官会扫）

条目里至少出现三条可点名证据：

1. **坏例回放进 CI**（A6/A9-e 路径）
2. **MCP≠A2A**（B2 DESIGN + 负例）
3. **checkpoint 数据 ≠ Durable 续跑 / 副作用幂等**（A2/B1）

不要写成「熟悉 LangGraph、MCP、Temporal」清单。

## E. 暂缓（加分不挡投）

- B3 compaction 硬字段负例
- 真 kill Worker 续跑录像
- symlink 逃逸、HITL 令牌续签（跟架构侧 G7 follow-up）

---

**维护**：Agent工程师；随 Mock 场次更新挂科句。  
**状态**：2026-09-13 首版（R1/R2 通过后）。
