# Lesson 10 — KB_SEARCH 工具化（RAG 进入 Agent）

## 关键变化

| 之前（07–09） | 现在（10） |
|---------------|------------|
| 脚本先检索再问模型 | 模型自己决定是否/何时检索 |
| 检索在循环外 | `KB_SEARCH` 是 tool_calls 的一环 |
| 一次检索一次生成 | 可多轮检索，再用 `finish` 收尾 |

这才是 JD 里常见的「Agentic RAG」雏形。

## 怎么跑

```bash
cd agent-learning-path && git pull
source .venv/bin/activate
export AGENTROUTER_API_KEY=...
export AGENTROUTER_BASE_URL=https://agentrouter.org/v1
export AGENTROUTER_MODEL=deepseek-v4-flash
python 01-foundations/11-rag-as-tool/kb_tool_agent.py
```

## 观察点

- 模型是否先 `KB_SEARCH` 再 `finish`
- 库外问题（火星年假）是否在 finish 里承认不知道
- trace 里工具顺序是否合理

## 下一课

LangGraph（或手写状态图）把「检索 / 回答 / 结束」画成显式节点。
