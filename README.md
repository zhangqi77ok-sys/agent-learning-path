# Agent Learning Path

面向有 Java 后端经验、转向 **AI Agent / LLM 应用工程**（中国市场）的实战教程仓库。

> 主作品栈：Python + OpenAI 兼容 API（AgentRouter / DeepSeek 等）+ 手写 Agent Loop → 后续 RAG / LangGraph  
> Java 作为生产接入与差异化，不作为唯一作品语言。

## 环境

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install openai
cp .env.example .env        # 填入自己的 Key，勿提交
export $(grep -v '^#' .env | xargs)  # 或按系统自行设置环境变量
```

## 课程进度

| 课 | 目录 | 内容 |
|----|------|------|
| 0 | `lesson00/` | 最小 Chat Completions 调用 |
| 1 | `lesson01/` | 流式输出 |
| 2 | `lesson02/` | 多轮 messages + 短期记忆 |
| 3 | `lesson03/` | Function Calling |
| 4 | `lesson04/` | while 版 Agent Loop + max_steps |
| 5 | `lesson05/` | 结束条件：no_tool_calls / finish / return_direct |
| 6 | `lesson06/` | 迷你 Trace（本地 JSON spans） |
| 7 | `lesson07/` | RAG 入门：切分 + 检索 + 带引用回答 |
| 8 | `lesson08/` | Embedding 向量检索，对比关键词 RAG |
| 9 | `lesson09/` | 混合检索：关键词 + 向量 + RRF |
| 后续 | — | RAG 工具化进 Agent → LangGraph → MCP |

详细学习手册见 `docs/java-to-agent-learning-handbook.md`（部分口径已按「Python 主作品」更新，以本 README 与各课为准）。

## 安全

- **永远不要**把 API Key 提交到 Git 或粘贴到聊天
- 使用环境变量或本地 `.env`（已在 `.gitignore`）
