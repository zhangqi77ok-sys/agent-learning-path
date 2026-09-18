import os
from openai import OpenAI

api_key = os.environ.get("AGENTROUTER_API_KEY")
base_url = os.environ.get("AGENTROUTER_BASE_URL", "https://agentrouter.org/v1")
model = os.environ.get("AGENTROUTER_MODEL", "deepseek-v4-flash")

if not api_key:
    raise SystemExit("缺少环境变量 AGENTROUTER_API_KEY")

client = OpenAI(api_key=api_key, base_url=base_url)

stream = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": "你是简洁的助教，用中文回答。"},
        {"role": "user", "content": "用三句话说明 RAG 在做什么。"},
    ],
    temperature=0.2,
    stream=True,
)

full_text = []
for chunk in stream:
    delta = chunk.choices[0].delta
    if delta and delta.content:
        full_text.append(delta.content)
        print(delta.content, end="", flush=True)

print("\n---")
print("拼起来的全文长度:", len("".join(full_text)))
