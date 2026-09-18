"""
Lesson 13 — MCP Client + 最小 Agent Loop

流程：
1) 通过 MCP stdio 拉起 mcp_kb_server.py
2) list_tools 发现工具
3) 聊天模型若要检索，就 call_tool('kb_search', ...)
4) 把工具结果回灌，再让模型给出最终答案

依赖：pip install mcp openai
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

api_key = os.environ.get("AGENTROUTER_API_KEY")
base_url = os.environ.get("AGENTROUTER_BASE_URL", "https://agentrouter.org/v1")
model = os.environ.get("AGENTROUTER_MODEL", "deepseek-v4-flash")
if not api_key:
    raise SystemExit("缺少环境变量 AGENTROUTER_API_KEY")

client = OpenAI(api_key=api_key, base_url=base_url)
SERVER = Path(__file__).resolve().parent / "mcp_kb_server.py"


def to_openai_tools(mcp_tools) -> list[dict]:
    """把 MCP tool schema 转成 OpenAI function tools。"""
    out = []
    for t in mcp_tools:
        out.append(
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": t.inputSchema
                    or {"type": "object", "properties": {}},
                },
            }
        )
    return out


async def run_once(question: str) -> None:
    params = StdioServerParameters(
        command="python",
        args=[str(SERVER)],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            print("MCP 发现的工具:", [t.name for t in listed.tools])

            tools = to_openai_tools(listed.tools)
            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是企业助手。需要公司知识时调用 kb_search；"
                        "没有证据就说不知道。最后给出中文结论。"
                    ),
                },
                {"role": "user", "content": question},
            ]

            for step in range(1, 5):
                print(f"\n=== loop step {step} ===")
                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )
                msg = resp.choices[0].message
                messages.append(msg)

                if not msg.tool_calls:
                    print("最终回答:", msg.content)
                    return

                for call in msg.tool_calls:
                    name = call.function.name
                    args = json.loads(call.function.arguments or "{}")
                    print(f"调用 MCP 工具: {name}({args})")
                    result = await session.call_tool(name, args)
                    # MCP 返回 content 列表；教学里拼成文本
                    text_parts = []
                    for item in result.content:
                        if hasattr(item, "text"):
                            text_parts.append(item.text)
                        else:
                            text_parts.append(str(item))
                    tool_text = "\n".join(text_parts)
                    print("工具结果:", tool_text[:300], "...")
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": tool_text,
                        }
                    )

            print("达到 max steps")


async def main() -> None:
    for q in ["带薪年假有几天？", "火星报销怎么做？"]:
        print("\n" + "#" * 64)
        print("用户:", q)
        await run_once(q)


if __name__ == "__main__":
    asyncio.run(main())
