# Agent Learning Path

面向有 Java 后端经验、转向 **AI Agent / LLM 应用工程**（中国市场）的实战学习仓库。

## 主路径：进阶主线（3–5 年岗）

> **招聘达标请走这条。** stage-01～04 与 Curriculum v2 仅作预修。

- 能力矩阵：`docs/capability-matrix-3to5y.md`
- 深挖题库（15 + 过不了就别去面 10）：`docs/interview-deep-dive-v2.md`
- 进阶课纲 A1–A9 + Capstone：`docs/curriculum-advanced-3to5y.md`
- JD 调研（含具名公开岗位模式）：`docs/jd-research-advanced-3to5y.md`

作品集硬门槛：租户隔离、HITL 外部写幂等、越权拦截、死循环熔断、失败 Trace 回放进评测集。缺一项 = 3–5 年岗未过。

## 预修：Curriculum v2（stage-01～04）

见 `docs/curriculum-v2.md`。PR #5（LangGraph HITL）按预修通过、按 3–5 年岗未过。

## 遗留参考

`lesson00`–`lesson14` 为早期练习，不作为主进度。

## 环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 安全

永远不要把 API Key 提交到 Git。
