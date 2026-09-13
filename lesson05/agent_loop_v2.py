import json
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from openai import OpenAI

api_key = os.environ.get("AGENTROUTER_API_KEY")
base_url = os.environ.get("AGENTROUTER_BASE_URL", "https://agentrouter.org/v1")
model = os.environ.get("AGENTROUTER_MODEL", "deepseek-v4-flash")
if not api_key:
    raise SystemExit("缺少环境变量 AGENTROUTER_API_KEY")

client = OpenAI(api_key=api_key, base_url=base_url)
RETURN_DIRECT_TOOLS = {"render_report"}


def get_time(city: str) -> str:
    mapping = {"北京": "Asia/Shanghai", "东京": "Asia/Tokyo", "纽约": "America/New_York"}
    tz = mapping.get(city)
    if not tz:
        return json.dumps({"error": f"不支持的城市: {city}"}, ensure_ascii=False)
    now = datetime.now(ZoneInfo(tz))
    return json.dumps({"city": city, "datetime": now.isoformat(timespec="seconds"), "tz": tz}, ensure_ascii=False)


def render_report(title: str, body: str) -> str:
    return json.dumps({"report": f"# {title}\n\n{body}\n"}, ensure_ascii=False)


def finish(answer: str) -> str:
    return json.dumps({"ok": True, "answer": answer}, ensure_ascii=False)


TOOL_IMPL = {
    "get_time": lambda a: get_time(a["city"]),
    "render_report": lambda a: render_report(a["title"], a["body"]),
    "finish": lambda a: finish(a["answer"]),
}

tools = [
    {"type": "function", "function": {
        "name": "get_time", "description": "查询城市当前时间",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    }},
    {"type": "function", "function": {
        "name": "render_report",
        "description": "生成给用户看的最终报告。调用后循环应直接结束，不必再总结。",
        "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "body": {"type": "string"}}, "required": ["title", "body"]},
    }},
    {"type": "function", "function": {
        "name": "finish", "description": "任务完成时调用，提交最终中文答案。",
        "parameters": {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"]},
    }},
]


def run_agent(user_text: str, max_steps: int = 8) -> dict:
    messages = [{
        "role": "system",
        "content": "你是助教。需要时间就调 get_time。若要输出成品报告，调 render_report。若用自然语言收尾，必须调 finish(answer=...)。不要编造工具结果。",
    }, {"role": "user", "content": user_text}]
    trace = []

    for step in range(1, max_steps + 1):
        t0 = time.time()
        resp = client.chat.completions.create(model=model, messages=messages, tools=tools, tool_choice="auto")
        msg = resp.choices[0].message
        messages.append(msg)
        latency_ms = int((time.time() - t0) * 1000)

        if not msg.tool_calls:
            result = {"stop_reason": "no_tool_calls", "final": msg.content or "", "steps": step, "trace": trace}
            print("停止原因: no_tool_calls"); print("最终:", result["final"]); return result

        direct_payload = None
        finished_payload = None
        for call in msg.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments or "{}")
            print(f"[step {step}] 调用 {name}({args})  llm_latency={latency_ms}ms")
            try:
                content = TOOL_IMPL[name](args)
            except Exception as e:
                content = json.dumps({"error": str(e)}, ensure_ascii=False)
            print(f"[step {step}] 结果 {content}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": content})
            trace.append({"step": step, "tool": name, "args": args, "content": content, "llm_latency_ms": latency_ms})
            if name == "finish":
                finished_payload = json.loads(content)
            if name in RETURN_DIRECT_TOOLS:
                parsed = json.loads(content)
                direct_payload = parsed.get("report") or content

        if finished_payload is not None:
            result = {"stop_reason": "finish_tool", "final": finished_payload.get("answer", ""), "steps": step, "trace": trace}
            print("停止原因: finish_tool"); print("最终:", result["final"]); return result

        names = [c.function.name for c in msg.tool_calls]
        if direct_payload is not None and all(n in RETURN_DIRECT_TOOLS for n in names):
            result = {"stop_reason": "return_direct", "final": direct_payload, "steps": step, "trace": trace}
            print("停止原因: return_direct"); print("最终:\n", result["final"]); return result

    return {"stop_reason": "max_steps", "final": "达到 max_steps，强制停止。", "steps": max_steps, "trace": trace}


if __name__ == "__main__":
    print("\n===== 场景 A：finish =====")
    run_agent("查一下北京现在时间，然后用 finish 给出一句话结论。")
    print("\n===== 场景 B：return_direct =====")
    run_agent("查东京时间，然后调用 render_report 生成标题为『东京时间简报』的短报告，正文包含查到的时间。")
