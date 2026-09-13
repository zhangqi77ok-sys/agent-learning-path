# A2 跑通证据

日期：2026-09-13  
命令：`python demo.py`

```text
=== demo1: O1 crash after external, resume without second call ===
crashed: injected_crash_after_external
external_calls_before_resume: 1
external_calls_total: 1 SLO_ok_idempotent: True
=== demo2: dual worker lease ===
{'status': 'lease_denied', ...}
SLO_ok_lease: True
=== demo3: cancel before finalize ===
{'status': 'cancelled', ...}
SLO_ok_cancel: True
```

对照 A2 SLO：重复 resume 外部 mock = 1；lease 互斥；cancel 生效。
