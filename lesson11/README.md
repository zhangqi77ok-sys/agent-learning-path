# Lesson 11 — 手写状态图（LangGraph 心智）

## 和上一课的区别

| Lesson 10 | Lesson 11 |
|-----------|-----------|
| Agent 隐式 while + tool_calls | 显式节点与边 |
| 模型临时决定调不调工具 | 图事先规定：先 retrieve 再 generate |
| 灵活，但流程难审计 | 流程可画、可测、可加条件边 |

仍是 **单 Agent / 单模型流水线**，不是 Multi-Agent。  
但节点以后可以替换成不同 Agent（检索员 / 回答员），那时才升级成多 Agent。

## 图

```text
START → retrieve → generate → END
```

## 怎么跑

```bash
cd agent-learning-path && git pull
source .venv/bin/activate
export AGENTROUTER_API_KEY=...
export AGENTROUTER_BASE_URL=https://agentrouter.org/v1
export AGENTROUTER_MODEL=deepseek-v4-flash
python lesson11/state_graph_rag.py
```

## 观察点

- 控制台是否固定打印 `→ node retrieve` 再 `→ node generate`
- `trace` 字段能否当作简易审计日志
- 对比 Lesson 10：这里模型不能跳过检索直接 finish

## 下一课

条件边：证据不足时回流再检索；并引出 Multi-Agent（检索员 / 回答员拆分）。
