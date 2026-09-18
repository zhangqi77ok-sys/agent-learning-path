# 进阶 JD 调研：3–5 年 AI Agent 应用 / 后端（公开猎聘向）

> 用途：驱动 [能力矩阵](/docs/capability-matrix.md)、[进阶课纲](/docs/curriculum.md)、[深挖题 v2](/docs/prep/interview-deep-dive.md)。  
> 性质：**公开岗位描述的共性归纳**（猎聘等可复核链接），**不是** Boss 直聘私有抓取，也不代表已投递结果。  
> 禁忌：不编造薪资统计、编制、通过率；下文若出现岗位页上的薪资区间，仅作「该条 JD 原文可见信息」，不作市场均值。

入门岗画像仍见仓库旧文 `docs/prep/jd-research-boss.md`。**3–5 年岗已上移到 Runtime / Harness / 长任务一致性 / 沙箱 / Eval 回归 / 私有化。**

---

## 具名公开来源（可复核）

| 简称 | 公开页（猎聘向） | 对进阶课的硬信号 |
|------|------------------|------------------|
| **瓴知 · Harness 高级研发** | [liepin.com/job/1984979153](https://www.liepin.com/job/1984979153.shtml)（及同司 [1985069621](https://www.liepin.com/job/1985069621.shtml)） | Runtime State / Checkpoint / Rollback / Commit；多层 Memory；MCP；**四层评测**（Model / Framework / Harness / Application）；Failure Mode；分布式与沙箱 |
| **了不起 · Runtime / Harness** | [liepin.com/job/1984625369](https://www.liepin.com/job/1984625369.shtml) | Harness：编排、状态持久化、断点续跑、失败恢复、HITL；Tool Sandbox；Guardrail / 审计；**Tracing + Eval 回归**；异步队列与状态机；权限边界 |
| **格创东智 · Agent 后端** | [liepin.com/job/1985241561](https://www.liepin.com/job/1985241561.shtml)（厂务 Agent 后端高级） | **Java + Python**；运行时 / Skill / 任务编排；模型切换与 Token 监控；**MQ / Redis / 向量库**；评测治理；**私有化部署**、项目隔离、权限审计 |
| **信华信 · 应用开发** | [liepin.com/job/1984888529](https://www.liepin.com/job/1984888529.shtml) | Agent Framework / Runtime 二次开发；Skill / Memory / MCP；MQ 等后端；能独立上线 |
| **财开 · 智能体** | [liepin.com/job/1984641235](https://www.liepin.com/job/1984641235.shtml)（浙财数智—AI智能体开发） | LangGraph / RAG / Function Calling / MCP / Skills；上下文工程；向量检索；偏应用落地与全栈 |

### 辅助对照（非「具名五家」但同方向）

| 来源 | 链接 | 信号 |
|------|------|------|
| 小红书 · Agent Harness | [job.xiaohongshu.com/.../20778](https://job.xiaohongshu.com/social/position/20778) | Runtime + Serverless；Trace/Log/Metric/Event；权限穿透；Multi-Agent |
| 天鹅到家 · Runtime & Harness 架构师 | [liepin.com/job/1984757783](https://www.liepin.com/job/1984757783.shtml) | `Model + Harness = Agent`；多租户；Tool Registry；Eval Pass Rate 红线；实事故障类型 |
| 字节跳动 · Agent 研发（集团信息系统，3–5 年） | [liepin.com/job/1985232731](https://www.liepin.com/job/1985232731.shtml) | 运行时、上下文工程、工具编排、企业身份、评测自进化、**独立推进**；Harness/沙箱/可观测/高并发优先 |
| 字节跳动 · Agent 开发（AI Coding / Coze） | [liepin.com/job/1983380283](https://www.liepin.com/job/1983380283.shtml) | 上下文工程、Multi-Agent、高并发低延迟、效果评测 |

---

## 能力交集（写进课纲的「硬关键词」）

从具名五家 + 辅助对照抽出、**反复出现**的工程能力（按主题，不按公司堆砌）：

1. **Runtime State / Checkpoint / Rollback（及 Commit）**  
   长链任务可恢复；状态机不是「内存里的 dict」。
2. **长任务续跑 + HITL**  
   断点、人工接管、失败恢复；了不起 JD 写得很直白。
3. **Tool Sandbox + Guardrail + 审计**  
   工具封装内部系统时默认危险；要沙箱与高风险拦截。
4. **Eval / Regression / Tracing**  
   质量可量化；回归能拦住；链路可追。瓴知明确到「四层」。
5. **Java + MQ + 向量库 + 私有化**  
   格创东智典型：企业交付不是纯 Python notebook；要中间件与本地化部署。
6. **MCP / Skill 注册与版本**  
   工具/技能平台化，而不是每个 Agent 硬编码。
7. **上下文工程与所有权**  
   字节类 JD：能独立扛方向，而不是只会接框架 API。

**语言画像**：Agent 执行侧 Python（或 Go）为主；**业务网关 / 工业与政企交付**大量要 Java；转岗者应用「Java 控边界、Python 跑 Harness」。

---

## 面试官真正在筛的（进阶版）

相对入门三问（边界 / 编排 / 效果），3–5 年多四刀：

| 刀 | 不过的样子 | 过的样子 |
|----|------------|----------|
| 一致性 | 「checkpoint 回滚了就没事」 | 分清状态回滚 vs 外部副作用；账本 / Saga |
| 多租户 | 「State 里有 tenant」 | 身份注入 + 检索前 ACL + 负例测试 |
| 工具供应链 | 「我们用了 MCP」 | 钉版本、指纹、投毒防御、沙箱 |
| 发布 | 「线下分涨了」 | 硬门禁 + holdout + 金丝雀 + 回滚 |

完整口试见 [过不了就别去面](/docs/prep/interview-deep-dive.md#gate)。

---

## 与仓库现状的差距

| 仓库（阶段 ①–④） | 具名 JD 已要求 |
|------------------|----------------|
| `MemorySaver` + 单机 HITL | PG/外部 checkpoint、租约、审批身份与过期 |
| 工具重试直觉 | Sandbox、幂等账本、取消/补偿 |
| 单库检索 + 引用 | ACL/RLS、版本与过期、历史可复现 |
| 无 MCP 治理 | Registry、schema 指纹、Skill 版本 |
| 无 Eval 门禁 | 四层评测、回归、Trace 闭环 |
| 无 Spring | Java 网关、MQ、私有化交付叙事 |

差距清单固化为课纲 [10 个死亡坑](/docs/curriculum.md#holes)。

---

## 使用约定

- 投递前用本页关键词对照简历与 Capstone，缺哪块补哪块。  
- 引用 JD 时写「公开岗位描述共性」，不要声称「Boss 已验证」。  
- 岗位页会改、会下架；链接失效时以公司名 + 岗位关键词检索复核，**不要臆造职责**。
