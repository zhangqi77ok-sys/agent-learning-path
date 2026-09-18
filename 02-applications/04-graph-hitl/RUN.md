# Stage 04 跑通证据
日期：2026-09-13  
LangGraph：1.2.11  
模型：`grok-4.6`  
命令：`python graph_app.py`
```text
=== invoke until interrupt ===
interrupted: True
next_nodes: ('approval_gate',)
effects_before_resume: ['researcher_ran:...', 'writer_ran']
=== resume with approved=True ===
final: 【已批准】 ...
effects_after_resume: ['researcher_ran:...', 'writer_ran', 'human_decided:True', 'finalize_ran']
side_effect_ok: True
```
结论：图在 `approval_gate` 暂停；`Command(resume=...)` 恢复后 researcher/writer 没有重复执行。
