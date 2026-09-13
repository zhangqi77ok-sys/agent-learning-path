# A2 · 长任务一致性（Checkpoint / Ledger / Outbox / Lease）

对照 `docs/curriculum-advanced-3to5y.md` A2、口试 O1–O3。

## 硬概念

- **Checkpoint** 恢复的是图/进度，不是外部世界。
- **Effect ledger** 才是副作用真相源；幂等键 `(tenant, thread, effect_key)`。
- **Outbox** 把「要通知下游」与业务提交绑定（本课 SQLite；生产用 PG 同事务）。
- **Worker lease**：同一 `run_id` 同时只被一个 Worker 持有。

本课用 **SQLite** 演示耐久语义；生产换 Postgres，约束与 API 不变。

## 运行

```bash
cd curriculum/advanced/A2-long-task
python demo.py
```

## 故障注入

1. tool/外部调用成功后进程崩溃，再 resume → 外部 mock 仍只调用 1 次  
2. 双 Worker 抢 lease → 后者 `lease_denied`  
3. cancel → 状态 `cancelled`

## 交付清单

- [x] store.py / engine.py / demo.py
- [x] PASS / RUN
