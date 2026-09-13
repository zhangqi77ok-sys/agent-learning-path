# Agent Learning Path

面向有 **Java 后端**经验、转向国内市场 **AI Agent / Agent 应用工程（约 3–5 年岗）** 的实战仓库：控制面代码 + 故障注入 + 模拟面试全文 + 简历差异化要点。

> GitHub About 简介已同步为进阶主线（不再是 lesson00–06）。

## 主路径：进阶主线（招聘达标）

| 材料 | 路径 |
|------|------|
| 能力矩阵 | `docs/capability-matrix-3to5y.md` |
| 深挖题库 | `docs/interview-deep-dive-v2.md` |
| 进阶课纲 A1–A9 | `docs/curriculum-advanced-3to5y.md` |
| JD 调研 | `docs/jd-research-advanced-3to5y.md` |
| 团队进度 | `docs/team-decisions-and-status.md` |
| 模拟面试 R1–R3 | `docs/mock-interviews/` |
| 计时练习包 | `docs/mock-interviews/timed-practice-pack-o10-g1.md` |
| 简历三条差异化 | `docs/resume-differentials.md` |
| 简历扩展 +12 | `docs/resume-bullets-extended.md` |
| 深挖必追问 | `docs/deep-dive-must-ask.md` |
| B1 Durable 调研 | `docs/b1-durable-runtime-research.md` |
| Trace 面试旁注 | `docs/mock-interviews/trace-interview-notes.md` |

实现目录：`curriculum/advanced/A1-runtime` … `A9-capstone`，以及 `B1-durable-runtime`、`B2-a2a`。

**作品集硬门槛**：租户隔离、HITL 外部写幂等、越权拦截、死循环熔断、失败 Trace 回放进评测。缺一项 = 3–5 年岗未过。

## Trace 面试口径

见 [`docs/mock-interviews/trace-interview-notes.md`](docs/mock-interviews/trace-interview-notes.md)：跨 Gateway→Java；按 span 定层；缺 `retrieve.filter` 硬否决。

## 预修 / 遗留

- Curriculum v2（stage-01～04）：`docs/curriculum-v2.md`（预修）
- `lesson00`–`lesson14`：早期练习，不作为主进度

## 环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 安全

永远不要把 API Key 提交到 Git。
