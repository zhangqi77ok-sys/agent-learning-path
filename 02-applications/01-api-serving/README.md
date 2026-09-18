# Stage 01 · LLM API / 工程地基

对照 JD：Python / FastAPI / 大模型 API。

## 目标

- 用 **OpenAI 兼容中转站** 稳定打通 Chat Completions
- Key 只进环境变量 / 本地 `.env`，不进仓库
- 能看清 model、token、耗时

## 配置

仓库根目录：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`（第三方中转站示例）：

```bash
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://your-relay.example/v1
OPENAI_MODEL=gpt-4o-mini   # 以中转站实际模型名为准
```

> 部分中转站会拦「通用客户端」。若出现 `unauthorized client`，换真正开放 Chat Completions 的兼容网关（或官方 DeepSeek 等），不要把 Key 写进代码。

## 运行

```bash
# CLI 一次调用
python 02-applications/01-api-serving/chat_once.py

# FastAPI 服务
cd 02-applications/01-api-serving && uvicorn app:app --reload --port 8001
```

健康检查：`GET http://127.0.0.1:8001/health`  
对话：`POST http://127.0.0.1:8001/v1/chat` body `{"message":"用一句话解释什么是 AI Agent"}`


> 跑通备注：`OPENAI_BASE_URL` 需带 `/v1`；本阶段实测模型名为 `grok-4.6`（不是 `grok4.6`）。

## 过关题作答

见 [PASS.md](./PASS.md)。

## 本阶段交付清单

- [x] `chat_once.py` / `app.py` 可配置 `base_url`
- [x] README（无密钥）
- [x] PASS.md 书面作答
- [x] 跑通证据（日志摘录，无 Key）——见 [RUN.md](./RUN.md)
