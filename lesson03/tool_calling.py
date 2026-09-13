import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from openai import OpenAI

api_key = os.environ.get("AGENTROUTER_API_KEY")
base_url = os.environ.get("AGENTROUTER_BASE_URL", "https://agentrouter.org/v1")
model = os.environ.get("AGENTROUTER_MODEL", "deepseek-v4-flash")
if not api_key:
    raise SystemExit("缺少环境变量 AGENTROUTER_API_KEY")

client = OpenAI(api_key=api_key, base_url=base_url)


def get_time(city: str) -> str:
    mapping = {"北京": "Asia/Shanghai", "上海": "Asia/Shanghai", "东京": "Asia/Tokyo", "纽约": "America/New_York"}
    tz_name = mapping.get(city)
    if not tz_name:
        return json.dumps({"error": f"不支持的城市: {city}"}, ensure_ascii=False)
    now = datetime.now(ZoneInfo(tz_name))
    return json.dumps({"city": city, "timezone": tz_name, "datetime": now.isoformat(timespec="seconds")}, ensure_ascii=False)


TOOL_IMPL = {"get_time": lambda args: get_time(args["city"])}
tools = [{
    "type": "function",
    "function": {
        "name": "get_time",
        "description": "查询某个城市的当前本地时间",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "城市名，如 北京、东京、纽约"}},
            "required": ["city"],
        },
    },
}]

messages = [
    {"role": "system", "content": "你是助教。需要时间信息时必须调用 get_time，不要自己编造。"},
    {"role": "user", "content": "现在北京和东京差几个小时？先查两个城市的时间再回答。"},
]

print("=== 第 1 次请求 ===")
resp = client.chat.completions.create(model=model, messages=messages, tools=tools, tool_choice="auto")
msg = resp.choices[0].message
messages.append(msg)

if msg.tool_calls:
    for call in msg.tool_calls:
        name = call.function.name
        args = json.loads(call.function.arguments or "{}")
        print(f"模型要调用: {name}({args})")
        result = TOOL_IMPL[name](args)
        print(f"工具返回: {result}")
        messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    print("\n=== 第 2 次请求 ===")
    resp2 = client.chat.completions.create(model=model, messages=messages, tools=tools)
    print("最终回答:", resp2.choices[0].message.content)
else:
    print("模型没调工具，直接答:", msg.content)
