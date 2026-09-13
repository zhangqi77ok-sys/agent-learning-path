# A2 跑通证据

日期：2026-09-13  
命令：`python demo.py`

关键断言：

```text
=== demo1a: crash BEFORE local ref (started, no ref) then resume ===
unique_tickets: 1  SLO_ok_no_double_effect: True
=== demo1b: crash AFTER local unknown+ref then resume ===
unique: 1 calls: 1
=== demo2: dual worker lease ===
lease_denied
=== demo3: cancel ===
cancelled
```

O1 补强：`started` 无 ref 路径用 Idempotency-Key + 对端查询，禁止裸重试。
