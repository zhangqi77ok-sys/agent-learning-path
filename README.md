# Agent Learning Path

面向有 **Java 后端**背景、转向 **AI Agent / Agent 应用工程** 的实战仓库。

这里不教怎么写 Prompt。它记录的是另一件事：一个 Agent 系统上线之前，**控制面**必须具备哪些能力，以及如何用可运行的代码把它们证明出来。

每个模块都遵循同一条证据链：**先注入故障，再拿 Trace / Eval 证明它不会再犯。**

---

## 快速验证

**不需要 API Key，不需要装任何依赖**（模块内部使用进程内 mock）。

```bash
git clone https://github.com/zhangqi77ok-sys/agent-learning-path.git
cd agent-learning-path

# 主作品：五段演示一跑到底，最后打印 ALL_OK
python 03-modules/A9-capstone/demo.py
```

一次跑完全部 11 个零依赖模块：

```bash
for m in 03-modules/*/ 04-frontier/B2-a2a/ projects/hotplug-harness/; do
  (cd "$m" && python demo.py | tail -1)
done
```

`02-applications/` 与 `04-frontier/B1-durable-runtime/` 需要额外依赖（见下方[环境](#环境)）。

---

## 模块地图

主线 A1–A9 是一条递进链：从单个 Run 的控制，到长任务、多租户、评测门禁，最后收束到 Capstone。

| 模块 | 主题 | 关键控制点 | 故障注入证据 |
|------|------|-----------|-------------|
| [A1](03-modules/A1-runtime/) | Runtime / Harness | Loop、工具白名单、预算、熔断、Replay | 死循环熔断 → `circuit_open`；越权工具拦截；预算耗尽停机 |
| [A2](03-modules/A2-long-task/) | 长任务一致性 | Checkpoint / Ledger / Outbox / Lease | 重复 resume → 外部副作用只发生 1 次 |
| [A3](03-modules/A3-tenant-auth/) | 租户 / RBAC / 审批 | 四键隔离、网关下发身份、HITL | 跨租户读 0 行；伪造 header 被拒；审批留审计 |
| [A4](03-modules/A4-advanced-rag/) | 进阶 RAG | 混合检索、版本过期、检索前 ACL | 过期文档不进上下文；跨租户不串答 |
| [A5](03-modules/A5-mcp-registry/) | MCP / Registry / 沙箱 | 工具指纹、版本治理、沙箱策略 | 工具变更可追溯；越界调用被沙箱挡下 |
| [A6](03-modules/A6-eval-otel/) | Eval + OTEL + 门禁 | 四层评测、发布红线、holdout | 失败 Trace 回放进回归集；残缺 fixture 禁入库 |
| [A7](03-modules/A7-model-gateway/) | 模型网关 | 按租户路由、预算、429 降级、缓存键 | 路由决策进 Trace；超预算可拒绝 |
| [A8](03-modules/A8-ha-platform/) | 高可用平台 | 队列、无状态 Runtime、隔离池、背压 | 双 Worker 争抢同一任务只成功一次 |
| [A9](03-modules/A9-capstone/) | **Capstone 主作品** | 端到端控制面 | 五段演示（见下） |

前沿对照：

| 模块 | 主题 | 说明 |
|------|------|------|
| [B1](04-frontier/B1-durable-runtime/) | Durable Runtime（Temporal） | Workflow / Activity / Signal 分工；Activity 幂等。**需装 `temporalio`** |
| [B2](04-frontier/B2-a2a/) | 最小 A2A | Agent 间委托：下行身份、幂等键、超时与取消 |

设计取舍与对照关系见 [`docs/curriculum.md`](docs/curriculum.md)，能力维度拆解见 [`docs/capability-matrix.md`](docs/capability-matrix.md)。

---

## 主作品：A9 Capstone

多租户企业 Agent 控制面，完整链路：**Java 鉴权 → Python Harness → 检索/工具/HITL → Outbox → Trace → Eval**。

`python 03-modules/A9-capstone/demo.py` 输出五段：

| 段 | 演示内容 | 判定 |
|----|---------|------|
| (a) | 四隔离键 + 跨租户访问 | `cross_tenant_rows = 0` |
| (b) | 已批准副作用的幂等 + Outbox | 重复 resume，`create_calls = 1` |
| (c) | 检索 ACL | 两个租户拿到各自答案，不串 |
| (d) | Loop 预算与熔断 | `circuit_open` / `budget_exhausted` |
| (e) | Trace → Bad Case → Eval 回放 | 脱敏 fixture；残缺样本禁入库 |

另有端到端可插拔项目 [`projects/hotplug-harness/`](projects/hotplug-harness/)：工具 / 模型 / 策略从 `plugins/` 热加载，不改核心循环即可扩展，附带 FastAPI + Vite 的 Q&A 控制台。

---

## 目录结构

```
01-foundations/     单概念最小实现：流式、记忆、工具调用、Agent Loop、
                    RAG 演进、状态图、Multi-Agent、MCP、评测
02-applications/    第一个能跑起来的服务：API 封装、工具循环、RAG 服务、
                    LangGraph + HITL（需 openai / fastapi / langgraph）
03-modules/         主线 A1–A9：生产级控制面模块（零依赖可跑）
04-frontier/        B1 Temporal、B2 A2A：与主流框架的对照实现
projects/           端到端作品（hotplug-harness）
docs/               课纲、能力矩阵、架构与 Java→Agent 迁移笔记
docs/prep/          备考材料：面试记录、JD 调研、简历要点、团队进度
```

---

## 环境

零依赖模块（A1–A9、B2、hotplug-harness）用系统 Python 即可跑。

需要联网或真实模型的部分：

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # openai / fastapi / mcp / langgraph
cp .env.example .env               # 填入中转站 Key 与 Base URL
```

B1 额外需要：

```bash
pip install temporalio
```

---

## 备考材料（附录）

求职向的面试记录、JD 调研与简历要点集中在 [`docs/prep/`](docs/prep/)，与主线的工程内容分开维护。

---

## 安全

不要把 API Key 提交到 Git。`.env` 已在 `.gitignore` 中；Trace 与 fixture 入库前做脱敏处理。

## License

MIT
