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
    mapping = {
        "北京": "Asia/Shanghai", "上海": "Asia/Shanghai", "东京": "Asia/Tokyo",
        "纽约": "America/New_York", "伦敦": "Europe/London",
    }
    tz_name = mapping.get(city)
    if not tz_name:
        return json.dumps({"error": f"不支持的城市: {city}"}, ensure_ascii=False)
    now = datetime.now(ZoneInfo(tz_name))
    return json.dumps({
        "city": city, "timezone": tz_name,
        "datetime": now.isoformat(timespec="seconds"), "utc_offset": now.strftime("%z"),
    }, ensure_ascii=False)


def add_numbers(a: float, b: float) -> str:
    return json.dumps({"a": a, "b": b, "sum": a + b}, ensure_ascii=False)


TOOL_IMPL = {
    "get_time": lambda args: get_time(args["city"]),
    "add_numbers": lambda args: add_numbers(float(args["a"]), float(args["b"])),
}

tools = [
    {"type": "function", "function": {
        "name": "get_time", "description": "查询城市当前本地时间",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    }},
    {"type": "function", "function": {
        "name": "add_numbers", "description": "计算两个数字相加",
        "parameters": {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}, "required": ["a", "b"]},
    }},
]


def run_agent(user_text: str, max_steps: int = 6) -> str:
    messages = [
        {"role": "system", "content": "你是助教。需要时间就调用 get_time，需要加法就调用 add_numbers。不要编造工具结果。信息够了再给出最终中文回答。"},
        {"role": "user", "content": user_text},
    ]

    for step in range(1, max_steps + 1):
        print(f"\n===== Loop step {step}/{max_steps} =====")
        resp = client.chat.completions.create(model=model, messages=messages, tools=tools, tool_choice="auto")
        msg = resp.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            final = msg.content or ""
            print("最终回答:", final)
            return final

        for call in msg.tool_calls:
            name = call.function.name
            raw_args = call.function.arguments or "{}"
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                args = {}
                result = json.dumps({"error": "arguments 不是合法 JSON", "raw": raw_args}, ensure_ascii=False)
            else:
                print(f"调用工具: {name}({args})")
                impl = TOOL_IMPL.get(name)
                if impl is None:
                    result = json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)
                else:
                    try:
                        result = impl(args)
                    except Exception as e:
                        result = json.dumps({"error": str(e)}, ensure_ascii=False)
            print(f"工具结果: {result}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    return "达到 max_steps，强制停止（防止死循环）。"


if __name__ == "__main__":
    run_agent("先查北京和纽约现在的时间，再计算 17.5 + 22.5，最后用三句话总结：两地时差大概多少、加法结果是多少。")
