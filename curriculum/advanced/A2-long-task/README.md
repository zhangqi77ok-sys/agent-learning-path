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

1. **O1a** 远端已成功、本地仍 `started` 无 ref → resume 先查对端 / 同 Idempotency-Key，不双开票  
2. **O1b** 本地已有 `unknown+ref` 后崩溃 → resume 只对账  
3. 双 Worker 抢 lease → 后者 `lease_denied`  
4. cancel → 状态 `cancelled`

## 交付清单

- [x] store.py / engine.py / demo.py
- [x] PASS / RUN
