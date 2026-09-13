"""LangGraph: researcher → writer → HITL approve → finalize (with checkpoints)."""
from __future__ import annotations
import operator
from typing import Annotated, Any, Literal, TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from openai import OpenAI
from client_config import load_config
KB = {
    "agent": "Agent = LLM + tools + loop；生产要权限、重试、Trace、评测。",
    "hitl": "Human-in-the-loop：关键副作用前暂停，等人批准再继续，避免重复执行。",
    "checkpoint": "Checkpoint 持久化图状态，恢复时从断点继续而不是重跑全部节点。",
}
class GraphState(TypedDict):
    query: str
    research: str
    draft: str
    approved: bool | None
    final: str
    effects: Annotated[list[str], operator.add]
def _llm(system: str, user: str) -> str:
    cfg = load_config()
    client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
    resp = client.chat.completions.create(model=cfg.model, messages=[{"role":"system","content":system},{"role":"user","content":user}], temperature=0.2)
    return resp.choices[0].message.content or ""
def researcher(state: GraphState) -> dict[str, Any]:
    q=state["query"]
    notes=[f"[{k}] {v}" for k,v in KB.items() if k in q.lower() or k in q] or ["[general] "+KB["agent"]]
    return {"research":"\n".join(notes),"effects":[f"researcher_ran:{q[:40]}"]}
def writer(state: GraphState) -> dict[str, Any]:
    draft=_llm("你是撰稿员。根据调研笔记写一段不超过120字的中文草案，注明依据关键词。",f"问题: {state['query']}\n笔记:\n{state['research']}")
    return {"draft":draft,"effects":["writer_ran"]}
def approval_gate(state: GraphState) -> dict[str, Any]:
    decision=interrupt({"type":"approve_draft","draft":state["draft"],"hint":"resume with Command(resume={'approved': True/False})"})
    approved=bool(decision.get("approved")) if isinstance(decision,dict) else bool(decision)
    return {"approved":approved,"effects":[f"human_decided:{approved}"]}
def route_after_approval(state: GraphState) -> Literal["finalize","rejected"]:
    return "finalize" if state.get("approved") else "rejected"
def finalize(state: GraphState) -> dict[str, Any]:
    return {"final":"【已批准】\n"+state["draft"],"effects":["finalize_ran"]}
def rejected(state: GraphState) -> dict[str, Any]:
    return {"final":"【已拒绝】草案未发布，无外部副作用。","effects":["rejected_ran"]}
def build_graph():
    g=StateGraph(GraphState)
    g.add_node("researcher",researcher); g.add_node("writer",writer); g.add_node("approval_gate",approval_gate); g.add_node("finalize",finalize); g.add_node("rejected",rejected)
    g.add_edge(START,"researcher"); g.add_edge("researcher","writer"); g.add_edge("writer","approval_gate")
    g.add_conditional_edges("approval_gate",route_after_approval,{"finalize":"finalize","rejected":"rejected"})
    g.add_edge("finalize",END); g.add_edge("rejected",END)
    return g.compile(checkpointer=MemorySaver())
def demo(approve: bool=True)->None:
    app=build_graph(); thread={"configurable":{"thread_id":"stage04-demo-1"}}; query="用 checkpoint 和 hitl 解释 Agent 生产落地要注意什么"
    print("=== invoke until interrupt ===")
    app.invoke({"query":query,"research":"","draft":"","approved":None,"final":"","effects":[]},config=thread)
    snap=app.get_state(thread)
    print("interrupted:",bool(snap.next)); print("next_nodes:",snap.next); print("draft_preview:",(snap.values.get("draft") or "")[:160]); print("effects_before_resume:",snap.values.get("effects"))
    print("=== resume with approved=%s ==="%approve)
    result=app.invoke(Command(resume={"approved":approve}),config=thread)
    print("final:",result.get("final")); print("effects_after_resume:",result.get("effects"))
    effects=result.get("effects") or []
    print("side_effect_ok:",effects.count("writer_ran")==1 and sum(1 for e in effects if str(e).startswith("researcher_ran:"))==1)
if __name__=="__main__": demo(approve=True)
