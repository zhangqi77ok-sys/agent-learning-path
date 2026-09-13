# Lesson 13 — MCP（Model Context Protocol）

## 安装

```bash
pip install mcp openai
```

## 跑客户端（会自动 stdio 拉起 server）

```bash
export AGENTROUTER_API_KEY=...
python lesson13/mcp_agent_client.py
```

也可单独起 server 观察：

```bash
python lesson13/mcp_kb_server.py
```
