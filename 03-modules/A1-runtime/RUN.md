# A1 跑通证据

日期：2026-09-13  
命令：`python demo.py`（无外部 LLM）

```text
=== demo1: happy path ===
succeeded steps 3 tools 2 final done
=== demo2: infinite same tool -> circuit_open ===
circuit_open steps 4 wall_ms 30.5
SLO_ok_circuit: True
=== demo3: forbidden tool blocked ===
failed blocked:tool_not_allowlisted:drop_db
=== demo4: budget max_steps ===
budget_exceeded steps 5
tool_spans 4 SLO_ok_budget: True
```

对照 A1 SLO：死循环 ≤8 step 进入 `circuit_open`；预算耗尽后无超额 tool span。
