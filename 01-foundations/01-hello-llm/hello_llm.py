import os
from openai import OpenAI

api_key = os.environ.get("AGENTROUTER_API_KEY")
base_url = os.environ.get("AGENTROUTER_BASE_URL", "https://agentrouter.org/v1")
model = os.environ.get("AGENTROUTER_MODEL", "deepseek-v4-flash")

if not api_key:
    raise SystemExit("缺少环境变量 AGENTROUTER_API_KEY")

client = OpenAI(api_key=api_key, base_url=base_url)

resp = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": "你是简洁的助教，用中文回答。"},
        {"role": "user", "content": "用一句话解释什么是 AI Agent。"},
    ],
    temperature=0.2,
)

print(resp.choices[0].message.content)
print("---")
print("model:", resp.model)
if resp.usage:
    print("tokens:", resp.usage.total_tokens)
