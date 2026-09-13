# Agent Learning Path

面向有 Java 后端经验、转向 **AI Agent / LLM 应用工程**（中国市场）的实战学习仓库。

## 主路径：Curriculum v2（Boss 直聘对标）

> **请按 v2 学与做。** 目标是达到大小厂「Agent 应用工程师」招聘要求，并完成可面试演示的作品集。

- 教程大纲：[docs/curriculum-v2.md](docs/curriculum-v2.md)
- JD 调研摘要：[docs/boss-jd-research.md](docs/boss-jd-research.md)
- 代码与练习目录：`curriculum/stage-01` … `stage-06`、`curriculum/portfolio`

## 环境（各阶段通用）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 填入中转站 base_url / model / key，勿提交
```

第三方 OpenAI 兼容中转站：在 `.env` 配置 `BASE_URL`、`API_KEY`、`MODEL`（具体变量名以各阶段 README 为准）。

## 安全

- **永远不要**把 API Key 提交到 Git 或粘贴到公开聊天
- 使用环境变量或本地 `.env`（已在 `.gitignore`）

## 遗留参考（非主进度）

`lesson00`–`lesson14` 为早期手写 Agent / RAG / MCP 练习，可作实现参考，**不作为主学习顺序**。旧手册见 `docs/java-to-agent-learning-handbook.md`。
