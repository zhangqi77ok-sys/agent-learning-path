import os
from openai import OpenAI

api_key = os.environ.get("AGENTROUTER_API_KEY")
base_url = os.environ.get("AGENTROUTER_BASE_URL", "https://agentrouter.org/v1")
model = os.environ.get("AGENTROUTER_MODEL", "deepseek-v4-flash")

if not api_key:
    raise SystemExit("缺少环境变量 AGENTROUTER_API_KEY")

client = OpenAI(api_key=api_key, base_url=base_url)

messages = [
    {"role": "system", "content": "你是助教。记住用户说过的偏好，回答尽量短。"}
]
MAX_TURNS = 6


def trim_messages(msgs, max_turns=MAX_TURNS):
    system = [m for m in msgs if m["role"] == "system"]
    rest = [m for m in msgs if m["role"] != "system"]
    keep = rest[-(max_turns * 2) :]
    return system + keep


print("多轮聊天已启动。输入 quit 退出。\n")

while True:
    user_text = input("你: ").strip()
    if user_text.lower() in {"quit", "exit", "q"}:
        break
    if not user_text:
        continue

    messages.append({"role": "user", "content": user_text})
    messages = trim_messages(messages)

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
    )
    reply = resp.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})

    print("助手:", reply)
    print(f"(当前 messages 条数: {len(messages)})\n")
