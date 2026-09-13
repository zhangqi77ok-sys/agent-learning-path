import json
import os
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from openai import OpenAI
from mini_trace import Trace


def load_api_key() -> str:
    key = os.environ.get("AGENTROUTER_API_KEY")
    if key:
        return key
    raise SystemExit("缺少环境变量 AGENTROUTER_API_KEY")



api_key = load_api_key()
base_url = os.environ.get("AGENTROUTER_BASE_URL", "https://agentrouter.org/v1")
model = os.environ.get("AGENTROUTER_MODEL", "deepseek-v4-flash")

client = OpenAI(api_key=api_key, base_url=base_url)
RETURN_DIRECT_TOOLS = {"render_report"}


def get_time(city: str) -> str:
    mapping = {"北京": "Asia/Shanghai", "东京": "Asia/Tokyo"}
    tz = mapping.get(city)
    if not tz:
        return json.dumps({"error": f"不支持: {city}"}, ensure_ascii=False)
    now = datetime.now(ZoneInfo(tz))
    return json.dumps(
        {"city": city, "datetime": now.isoformat(timespec="seconds")},
        ensure_ascii=False,
    )


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
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "查询城市当前时间",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_report",
            "description": "生成最终报告；调用后应直接结束",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["title", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "提交最终中文答案",
            "parameters": {
                "type": "object",
                "properties": {"answer": {"type": "string"}},
                "required": ["answer"],
            },
        },
    },
]


def run_agent(user_text: str, max_steps: int = 8) -> dict:
    tr = Trace(run_name="lesson06")
    messages = [
        {
            "role": "system",
            "content": (
                "你是助教。需要时间调 get_time；成品报告调 render_report；"
                "自然语言收尾必须调 finish。不要编造工具结果。"
            ),
        },
        {"role": "user", "content": user_text},
    ]

    for step in range(1, max_steps + 1):
        t0 = time.time()
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        latency_ms = int((time.time() - t0) * 1000)
        msg = resp.choices[0].message
        messages.append(msg)

        usage = getattr(resp, "usage", None)
        tr.span(
            "llm",
            step=step,
            latency_ms=latency_ms,
            has_tool_calls=bool(msg.tool_calls),
            messages_len=len(messages),
            prompt_tokens=getattr(usage, "prompt_tokens", None),
            completion_tokens=getattr(usage, "completion_tokens", None),
            content_preview=(msg.content or "")[:80],
            tool_names=[c.function.name for c in (msg.tool_calls or [])],
        )

        if not msg.tool_calls:
            path = tr.finish("no_tool_calls", msg.content or "", step)
            return {
                "stop_reason": "no_tool_calls",
                "final": msg.content or "",
                "trace_file": str(path),
            }

        direct_payload = None
        finished_payload = None

        for call in msg.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments or "{}")
            t1 = time.time()
            try:
                content = TOOL_IMPL[name](args)
            except Exception as e:
                content = json.dumps({"error": str(e)}, ensure_ascii=False)
            tool_ms = int((time.time() - t1) * 1000)

            messages.append({"role": "tool", "tool_call_id": call.id, "content": content})
            tr.span(
                "tool",
                step=step,
                name=name,
                args=args,
                latency_ms=tool_ms,
                content_preview=content[:120],
            )

            if name == "finish":
                finished_payload = json.loads(content)
            if name in RETURN_DIRECT_TOOLS:
                direct_payload = json.loads(content).get("report") or content

        if finished_payload is not None:
            final = finished_payload.get("answer", "")
            path = tr.finish("finish_tool", final, step)
            return {"stop_reason": "finish_tool", "final": final, "trace_file": str(path)}

        names = [c.function.name for c in msg.tool_calls]
        if direct_payload is not None and all(n in RETURN_DIRECT_TOOLS for n in names):
            path = tr.finish("return_direct", direct_payload, step)
            return {
                "stop_reason": "return_direct",
                "final": direct_payload,
                "trace_file": str(path),
            }

    path = tr.finish("max_steps", "达到 max_steps，强制停止。", max_steps)
    return {
        "stop_reason": "max_steps",
        "final": "达到 max_steps，强制停止。",
        "trace_file": str(path),
    }


if __name__ == "__main__":
    result = run_agent("查北京时间，再用 finish 给一句话结论。")
    print(
        "\nRESULT:",
        json.dumps(
            {k: result[k] for k in ("stop_reason", "trace_file")},
            ensure_ascii=False,
        ),
    )
    print("FINAL:", result["final"])
