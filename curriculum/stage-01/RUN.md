# Stage 01 跑通证据

日期：2026-09-13  
中转：`https://ss2a.top/v1`  
模型：`grok-4.6`  
命令：`python chat_once.py`（Key 仅环境变量）

```text
AI Agent 是一种能自主感知环境、推理规划并采取行动以实现目标的智能系统。
---
base_url: https://ss2a.top/v1
requested_model: grok-4.6
response_model: grok-4.6
latency_ms: 8524.1
tokens: prompt=217 completion=299 total=516
```

对照 JD：Python + OpenAI 兼容大模型 API 调用已打通；可观测到 latency 与 token。
