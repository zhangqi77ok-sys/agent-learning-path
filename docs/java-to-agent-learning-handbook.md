# Java → AI Agent 应用工程师：可执行学习手册

> 面向：4 年 Java 后端，目标中国市场 **LLM / Agent 应用开发岗**（工程化落地，不是算法岗）  
> 节奏：每天约 **1–2 小时**（按均值 1.5h ≈ 每周 10h）  
> 总周期建议：**6–8 个月**可稳定投递；冲刺可压到 5–6 个月  
> 主线技术：**Spring AI / Spring AI Alibaba（Java 主战）+ LangGraph 概念（面试通用）+ Python 够用即可**

---

## 0. 先对齐：你要投的是什么岗

**就是**完整工程化的应用开发岗，典型 JD 关键词：

- AI Agent 开发工程师 / 大模型应用开发 / 智能体研发
- RAG、Tool Calling、MCP、Memory、Multi-Agent
- 可观测性、评测、流式、限流、权限与安全
- Docker / 分布式 / 高可用（你四年 Java 正好用上）

**不是**：大模型算法岗（SFT/RLHF/DPO 为主、顶会论文导向）。那条线另开打法，本手册不走。

**双轨原则（强烈推荐）**

| 轨道 | 用途 | 占比 |
|------|------|------|
| Java + Spring AI Alibaba | 做可上线作品、写简历、讲架构 | 70% |
| Python + LangChain/LangGraph | 读懂主流生态、面试不卡壳 | 30% |

---

## 1. 每天怎么学（固定模板，防拖延）

每天 60–120 分钟建议拆成：

| 时段 | 时长 | 做什么 |
|------|------|--------|
| A. 输入 | 20–30 分钟 | 文档 / 教程 / 短文（只看当天主题） |
| B. 动手 | 40–70 分钟 | 写代码、改检索、跑 Agent、记指标 |
| C. 沉淀 | 10 分钟 | 半页笔记：今天踩坑 + 一个数字（延迟/召回/token） |

**铁律**

1. 每周至少 1 次可运行提交到 GitHub（哪怕很小）
2. 用 Cursor / Claude Code 写代码可以，但 **Spec（目标、约束、验收）自己写**
3. 资讯每天最多 15 分钟，别刷成主业（见第 8 章）

**周末（可选加时 2–4h）**

- 把本周 Demo 打磨成「能演示 + 能讲清为什么」
- 补一份 README：架构图、怎么跑、指标、已知问题

---

## 2. 总览时间表（按每天 1.5h）

| 阶段 | 周次 | 主题 | 可投递程度 |
|------|------|------|------------|
| P0 | 第 1 周 | 环境 + 心智模型 + 第一个流式 Chat API | 还不行 |
| P1 | 第 2–4 周 | Prompt + LLM 工程基础 | 还不行 |
| P2 | 第 5–12 周 | 生产级 RAG（核心作品 #1） | 小厂可试水 |
| P3 | 第 13–20 周 | Agent：Tool / MCP / Memory / 控制 | 中厂可投 |
| P4 | 第 21–26 周 | Multi-Agent + Graph 编排 | 作品成型 |
| P5 | 第 27–30 周 | 评测 / 可观测 / 成本 / 安全 / 部署 | 对标大厂业务线 |
| P6 | 第 31–32 周+ | 简历包装 + 面试题库 + 持续迭代 | 正式冲刺 |

时间不固定时：按「阶段完成」推进，别按日历焦虑。少学的周就少推进，别跳阶段。

---

## 3. 分阶段详解（学什么 / 在哪学 / 做什么 / 怎么算过）

### P0｜第 1 周：环境与第一个可运行服务

**学什么**

- Agent ≠ Chatbot：有目标、会用工具、会循环（Agent Loop）
- Token、上下文窗口、流式输出、模型路由直觉
- Java 侧：Spring Boot 3 + JDK 17+

**在哪学**

1. 概念入门（中文，先建立地图）  
   - Learn Agent：https://learnagent.wiki/  
   - Datawhale Hello-Agents：https://github.com/datawhalechina/hello-agents  
   - Hello-Agents PDF：仓库 Releases，或 https://www.datawhale.cn/learn/summary/239
2. Java 主框架官网  
   - Spring AI Alibaba：https://java2ai.com/  
   - 快速开始：https://java2ai.com/docs/quick-start
3. 模型 API（任选 1–2 个先通）  
   - 阿里云百炼 / DashScope（通义）  
   - DeepSeek 开放平台  
   - 硅基流动 / 其他 OpenAI 兼容网关（按你方便）

**做什么（本周交付）**

- [ ] 建 GitHub 仓库：`agent-learning-lab`
- [ ] Spring Boot 服务：`POST /chat` + SSE 流式回复
- [ ] 接一个真实模型 API（通义或 DeepSeek）
- [ ] README：如何配置 Key、如何 curl 调用

**验收**

- 本地能流式打字机输出
- Key 不进仓库（用环境变量）
- 你能口头解释：请求怎么到模型、流式怎么回前端

---

### P1｜第 2–4 周：Prompt 与 LLM 应用基础

**学什么**

- System / User / Tool 消息角色
- Few-shot、CoT、ReAct（先理解，后面 Agent 会用到）
- 结构化输出（JSON schema / 强制格式）
- 温度、max tokens、超时、重试

**在哪学**

1. Prompt 工程（官方优先）  
   - OpenAI Prompt engineering（英，短精）：https://platform.openai.com/docs/guides/prompt-engineering  
   - Anthropic Prompt 工程（英）：https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview  
   - 通义 / 各厂商文档里的「提示词最佳实践」章节
2. 中文体系化  
   - Hello-Agents 前几章（原理 + 范式）  
   - Learn Agent 卡片：ReAct、Agent vs Chatbot
3. Spring AI 文档  
   - Spring AI 官方：https://docs.spring.io/spring-ai/reference/  
   - ChatClient、PromptTemplate、Advisor 概念

**做什么**

- [ ] 同一业务问题写 3 版 Prompt，对比效果（准确率/啰嗦程度）
- [ ] 实现：结构化输出（如工单 JSON）
- [ ] 实现：简单会话记忆（最近 N 轮）
- [ ] 记一份「Prompt 实验表」（输入、策略、结果、成本）

**验收**

- 能讲清：为什么 ReAct 适合工具调用场景
- 能演示：无记忆 vs 有记忆的差异
- 简历可写：「完成 Prompt 实验与结构化输出服务」

---

### P2｜第 5–12 周：生产级 RAG（作品 #1，最重要）

**学什么（必须能讲清楚）**

- 文档解析 → Chunking → Embedding → 向量库
- 关键词检索（ES）+ 向量检索 + 融合（RRF）+ Rerank
- 查询改写、多知识库路由、引用溯源
- 权限隔离（按用户/租户过滤）
- 会话摘要记忆（控 token）

**在哪学**

1. RAG 原理与工程  
   - Learn Agent：RAG 卡片 https://learnagent.wiki/  
   - LlamaIndex 概念文档（英，检索理念很清晰）：https://docs.llamaindex.ai/  
   - LangChain RAG 教程（英/社区中文转载）：https://python.langchain.com/docs/tutorials/rag/
2. Java 实战路径  
   - Spring AI VectorStore / RAG Advisor 文档  
   - Spring AI Alibaba 教程站：https://java2ai.com/  
   - 开源参考（学架构，别整段抄）：  
     - alibaba/spring-ai-alibaba：https://github.com/alibaba/spring-ai-alibaba  
     - 企业级 Java Agentic RAG 项目可搜 GitHub：`ragent`、`DD_Rag`（看 README 技术点清单）
3. 向量库文档（选一个深挖）  
   - PgVector（和 Postgres 一体，上手快）  
   - Milvus：https://milvus.io/docs  
   - Elasticsearch 向量/全文能力文档
4. 评测入门  
   - Ragas：https://docs.ragas.io/  
   - 先会做「黄金问答集 + 人工抽检」，再上自动指标

**做什么（拆成小里程碑）**

| 周 | 目标 |
|----|------|
| 5–6 | 文档入库 Pipeline：PDF/Markdown → 切分 → Embedding → 入库 |
| 7–8 | 基础问答：TopK 召回 + Prompt 组装 + 带来源引用 |
| 9–10 | 混合检索 + Rerank；查询改写 |
| 11 | 权限过滤 + 会话摘要记忆 |
| 12 | 评测集 30–50 题；出一版指标报告；Docker 一键起 |

**项目建议命名**：`enterprise-kb-agent`（企业知识库助手）

**验收（面试官最爱问）**

- [ ] 能画架构图：入库链 / 查询链
- [ ] 能说清：切分策略为什么这样选、坏 case 怎么排查
- [ ] 有数字：某评测集上的命中率 / 延迟 / 单次 token 成本
- [ ] Demo 可现场跑，回答带引用

---

### P3｜第 13–20 周：Agent 核心（作品 #2 启动）

**学什么**

- Agent Loop：Thought → Act → Observe → …
- Function / Tool Calling：工具描述、参数校验、失败恢复
- MCP：工具发现、Client/Server、接到 Agent
- Memory：短期 / 长期 / 检索记忆
- 控制：最大轮次、终止条件、防死循环、超时熔断

**在哪学**

1. 官方与协议  
   - MCP 官网：https://modelcontextprotocol.io/  
   - Spring AI Alibaba ReactAgent 快速开始：https://java2ai.com/docs/quick-start  
   - Graph / MCP 节点教程：java2ai.com 文档中 Graph、MCP 章节
2. 框架对照（建立通用心智）  
   - LangGraph 文档：https://langchain-ai.github.io/langgraph/  
   - LangChain 中文社区（看讨论与踩坑）：https://www.langchain.cn/
3. 体系课/手册  
   - Hello-Agents（Agent 范式、Memory、评估章节）  
   - Agent Cookbook：https://agent-cookbook.com/zh  
   - AgentWay（偏 PoC 主线）：https://agentway.dev/zh
4. Java MCP 实战文（检索关键词）  
   - 「Spring AI Alibaba MCP」「ReactAgent MCP」系列技术博客（技术栈/掘金/知乎）

**做什么**

- [ ] 给知识库加 `KB_SEARCH` 工具（检索变成工具，而不是写死在 Service）
- [ ] 再加 2 个业务工具：如 `CREATE_TICKET`、`QUERY_ORDER`（可先 mock）
- [ ] 接一个 MCP Server（可先用公开 MCP，如地图/搜索类，再写自己的）
- [ ] 实现：recursionLimit、工具重试、错误信息回灌模型
- [ ] Trace：至少打印每轮 tool name / latency / token

**作品 #2 建议场景（选一个你熟的业务）**

- 内部工单助手
- 电商客服（查单 + 知识库 + 转人工）
- 运维排障助手（查日志 API + runbook RAG）

**验收**

- [ ] 现场演示：多轮对话中触发工具，失败能恢复
- [ ] 能讲：何时用单 Agent，何时不该上 Multi-Agent
- [ ] README 有序列图：一次完整 Tool Call 链路

---

### P4｜第 21–26 周：Multi-Agent 与编排

**学什么**

- 模式：Routing / Sequential / Parallel / Supervisor / Handoff
- Graph 状态、检查点、Human-in-the-loop
- Skills（可复用技能）与工具的边界
- 过度设计警惕：不是所有问题都需要多 Agent

**在哪学**

1. Spring AI Alibaba  
   - Multi-agent patterns 示例：https://github.com/alibaba/spring-ai-alibaba（examples）  
   - Graph 教程：https://java2ai.com/docs/…/graph/…
2. LangGraph  
   - Multi-agent 指南：LangGraph 官方 docs  
   - 对比阅读：同一模式在 Java Graph vs Python LangGraph 怎么表达
3. 概念卡片  
   - Learn Agent：Handoff、Testing Pyramid for Agents

**做什么**

- [ ] 实现 Supervisor + 2 个子 Agent（如：检索员 / 执行员 / 审核员 三角色里选）
- [ ] 加一个人机确认节点（高风险操作要人工点头）
- [ ] 导出 Mermaid/PlantUML 流程图进 README

**验收**

- [ ] 能讲清状态如何在节点间传递
- [ ] 有并行或路由的真实收益（延迟或质量），不是为了 Multi 而 Multi

---

### P5｜第 27–30 周：生产工程化（拉开候选人差距）

**学什么**

- 可观测：Trace、Prompt/Tool span、用户反馈回流
- Eval：黄金集、回归、线上抽检
- 成本：模型路由、缓存、排队
- 安全：Prompt 注入、越权、敏感信息、输出过滤
- 运行：SSE、限流、熔断、灰度、Docker/K8s 基础

**在哪学**

1. 可观测 / 评测  
   - Langfuse：https://langfuse.com/docs  
   - LangSmith（了解即可）：https://docs.smith.langchain.com/  
   - Ragas：https://docs.ragas.io/
2. 安全  
   - OWASP LLM Top 10（搜最新版）：了解注入、数据泄露、过度代理  
   - Learn Agent / AgentWay 的 Agent Security 专题
3. 工程  
   - 你已有的 Java 分布式经验直接迁移：网关限流、Redis 队列、超时重试  
   - 容器：Docker 官方文档 + 一份 compose 起全栈

**做什么**

- [ ] 两个作品都接入 Trace（至少 Langfuse 或自建日志结构）
- [ ] 写出《评测报告 v1》：集规模、指标、坏 case 分类
- [ ] 压测一页：并发、P95、错误率、成本估算
- [ ] 安全清单：鉴权透传、工具白名单、注入测试用例 10 条

**验收**

- 面试能像聊微服务一样聊 Agent：SLO、成本、故障排查路径

---

### P6｜第 31–32 周+：求职包装

**简历项目写法（模板）**

> 企业知识库 Agentic RAG（Java / Spring AI Alibaba）  
> - 混合检索（向量 + ES + RRF + Rerank），评测集 XX 题命中率从 A→B  
> - Tool Calling + 会话摘要记忆；P95 延迟 XXms；单次成本降 XX%  
> - Langfuse 全链路 Trace；Docker Compose 一键部署  

**面试高频题（每周练 3 题，口述 5 分钟）**

1. Agent Loop 怎么设计终止与容错？  
2. RAG 召回差，你的排查顺序？  
3. Tool 与 MCP 区别？如何做权限？  
4. 什么时候上 Multi-Agent？什么时候不要？  
5. 如何评测非确定性系统？  
6. 如何控制 token 成本与延迟？  
7. Prompt 注入怎么防？  
8. 和传统工作流引擎比，Agent 的边界在哪？

**投递策略**

- 作品 #1 完成后：AI 创业公司 / 中小厂应用岗
- 作品 #2 + 工程化完成后：大厂业务线 Agent（高德式 Java+Agent、腾讯 Agent 产品研发等）
- 投递标题对齐 JD：写「大模型应用 / Agent 开发」，别只写「Java 后端」

---

## 4. 工具与账号清单（第一周搞定）

| 类型 | 推荐 | 用途 |
|------|------|------|
| IDE | Cursor / IntelliJ + AI | 日常开发 |
| 语言 | JDK 17+、Maven；Python 3.11（辅助） | 主/辅 |
| 框架 | Spring Boot 3、Spring AI、Spring AI Alibaba | 主战 |
| 模型 | 通义 + DeepSeek（至少两个，方便对比） | 调用 |
| 向量库 | PgVector 或 Milvus | RAG |
| 检索 | Elasticsearch（可选但很加分） | 混合检索 |
| 可观测 | Langfuse | Trace / 评测协同 |
| 部署 | Docker Compose | 作品演示 |
| 版本 | GitHub 公开仓库 | 简历证据 |

---

## 5. 学习资源总表（按优先级）

### A. 主线必跟（收藏置顶）

1. https://java2ai.com/ — Spring AI Alibaba 官网与文档  
2. https://java2ai.com/docs/quick-start — ReactAgent 上手  
3. https://github.com/alibaba/spring-ai-alibaba — 源码与 examples  
4. https://docs.spring.io/spring-ai/reference/ — Spring AI 核心抽象  
5. https://github.com/datawhalechina/hello-agents — 中文系统教程  
6. https://learnagent.wiki/ — 概念卡片（Agent/MCP/RAG/评测）  
7. https://modelcontextprotocol.io/ — MCP 协议  
8. https://langchain-ai.github.io/langgraph/ — LangGraph（面试通用语言）

### B. 实战与扩展

- https://agent-cookbook.com/zh — Agent 实战教程库  
- https://agentway.dev/zh — 从会用到做出 PoC  
- https://www.langchain.cn/ — LangChain 中文社区讨论  
- https://python.langchain.com/docs/ — LangChain 官方（对照读）  
- https://docs.ragas.io/ — RAG/Agent 评测  
- https://langfuse.com/docs — 可观测性  

### C. 视频 / 课程（选一条跟完，别贪多）

- B 站搜：`Spring AI Alibaba`、`LangGraph 实战`、`RAG 企业知识库`（选最近一年、有完整项目的系列）  
- Datawhale 课程与公众号（跟 Hello-Agents 更新）  
- 阿里云开发者 / 百炼文档里的「应用搭建」示例  

**原则**：主线只跟 **一条 Java 文档站 + 一个中文体系教程 + 一个 LangGraph 对照**，其他当词典查。

---

## 6. 资讯：每天 15 分钟从哪里看「最新」

### 中文新闻（行业感知）

- 机器之心：https://www.jiqizhixin.com/  
- 量子位：https://www.qbitai.com/  

### 模型与开源动态

- Hugging Face Blog：https://huggingface.co/blog （可看中文区 https://huggingface.co/blog/zh）  
- HuggingFace 中国（下载与国内生态）：https://huggingfacechina.com/zh/  
- GitHub Trending（过滤 `agent` / `mcp` / `rag`）  
- 各模型厂 Changelog：OpenAI / Anthropic / DeepSeek / 通义 / 智谱 / Moonshot  

### 工程向深读（每周 1–2 篇即可）

- LangChain / LangGraph Blog  
- Anthropic Engineering / Claude 相关工程文  
- Spring AI Alibaba 博客与 Release：https://java2ai.com/  
- 知乎专栏 / 掘金：搜「Agentic RAG」「MCP」「上下文工程」（注意鉴日期，优先 2025–2026）

### 信息流用法（避免沉迷）

| 频率 | 动作 |
|------|------|
| 每天 10–15 分钟 | 机器之心或量子位扫标题 + 收藏 1 篇 |
| 每周日 30 分钟 | 写「本周 AI 工程笔记」：只有影响你技术栈的 3 条（新协议/新框架特性/可复用模式） |
| 每月 | 升级一次依赖（Spring AI / SAA 小版本），读 Release Note |

**只关心对工程有影响的**：新 Agent 框架能力、MCP/A2A 协议、RAG 新范式、评测与安全实践。融资新闻、模型跑分大战可以略读。

---

## 7. 社区与人脉（问问题、看真实坑）

| 社区 | 链接/入口 | 怎么用 |
|------|-----------|--------|
| Datawhale | GitHub org + 公众号 | Hello-Agents issue 提问、组队学习 |
| LangChain 中文社区 | https://www.langchain.cn/ | 搜同类报错、看 Agent 讨论 |
| GitHub Discussions/Issues | spring-ai-alibaba、LangGraph 等仓库 | 提 bug、读别人怎么用 |
| V2EX | v2ex.com 搜 Agent / 招聘 | 看市场口径与薪资帖 |
| 即刻 | 搜「AI 开发」「Agent」 | 短平快动态与工具安利 |
| 知乎 | 话题：大模型、RAG、Agent | 深度长文（注意鉴别广告课） |
| 掘金 / CSDN | 技术博文 | Java + Spring AI 实战文较多 |
| Discord/Slack | LangChain、各开源项目官方 | 英文为主，追新特性 |
| 微信群 | Datawhale、各课程/同城技术群 | 求职与内推信息（质量参差） |
| 本地 Meetup | 城市 Java/AI 线下 | 半年去 1–2 次就有价值 |

**提问模板（社区好感度高）**

1. 目标是什么（一句话）  
2. 技术栈与版本  
3. 已尝试过什么  
4. 期望结果 / 报错全文  

---

## 8. 每周检查清单（打印或置顶）

- [ ] 本周主题只围绕当前阶段（没飘去微调/扩散模型）  
- [ ] 有 Git 提交，README 有更新  
- [ ] 至少记录 1 个指标或 1 个坏 case  
- [ ] 资讯不超过每日 15 分钟  
- [ ] 用自己的话讲一遍本周学到的概念（录音 3 分钟也行）  

---

## 9. 风险与避坑

1. **只学 Dify/Coze 拖拽**：能演示，但深度岗面试容易挂；当作辅助，不作为唯一作品。  
2. **只调 API 不做检索/工具/评测**：会被当成「套壳」。  
3. **同时学 5 个框架**：选 Spring AI Alibaba 深挖，LangGraph 理解概念即可。  
4. **忽视 Java 老本行**：高并发、权限、稳定性恰恰是你对纯 Python 转行者的优势。  
5. **没有公开仓库**：中国市场很多 JD 直接要 GitHub / 可演示项目。  

---

## 10. 你现在立刻做的 3 件事（今天 1–2 小时）

1. 注册/准备：GitHub 仓库、模型 API Key、Cursor  
2. 打开 https://java2ai.com/docs/quick-start 跑通官方最小 ReactAgent  
3. 收藏本文资源表 A 类链接，资讯只订「机器之心 + java2ai Release」

---

*手册版本：2026-09 · 按中国市场 Agent 应用工程岗整理。框架版本迭代快，以各官网最新文档为准；学习主线不变：RAG → Tool/MCP → Agent → Multi-Agent → 评测与生产化。*
