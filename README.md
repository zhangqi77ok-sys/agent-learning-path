# Agent Learning Path

面向有 Java 后端经验、转向 **AI Agent / LLM 应用工程**（中国市场）的实战教程仓库。

> 主作品栈：Python + OpenAI 兼容 API（AgentRouter / DeepSeek 等）+ 手写 Agent Loop → 后续 RAG / LangGraph  
> Java 作为生产接入与差异化，不作为唯一作品语言。

## 环境

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt  # 或: pip install openai mcp
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
| 10 | `lesson10/` | KB_SEARCH 工具化，进入 Agent Loop |
| 11 | `lesson11/` | 手写状态图：retrieve → generate → END |
| 12 | `lesson12/` | 条件边 + 检索员/回答员 Multi-Agent |
| 13 | `lesson13/` | MCP：工具协议化（Server/Client） |
| 后续 | — | 评测/Trace 作品化 → 简历包装 |

详细学习手册见 `docs/java-to-agent-learning-handbook.md`（部分口径已按「Python 主作品」更新，以本 README 与各课为准）。

## 安全

- **永远不要**把 API Key 提交到 Git 或粘贴到聊天
- 使用环境变量或本地 `.env`（已在 `.gitignore`）
