# A7 · 模型网关 / 路由 / 成本

对照课纲 A7、深挖 Q9/Q10。

## 硬规则

- 路由键：`(tenant, task_class, sensitivity, budget_left)`。
- 429/5xx → fallback + 熔断；15s 内明确终态。
- 缓存键含 `tenant_id` + `acl_version`；跨租户串答 = 0。
- 预算耗尽不得打贵模型（premium）。

## 运行

```bash
cd 03-modules/A7-model-gateway
python demo.py
```
