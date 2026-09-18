# Lesson 13 — MCP（Model Context Protocol）

## 安装

```bash
pip install mcp openai
```

## 跑客户端（会自动 stdio 拉起 server）

```bash
export AGENTROUTER_API_KEY=...
python 01-foundations/14-mcp/mcp_agent_client.py
```

也可单独起 server 观察：

```bash
python 01-foundations/14-mcp/mcp_kb_server.py
```
