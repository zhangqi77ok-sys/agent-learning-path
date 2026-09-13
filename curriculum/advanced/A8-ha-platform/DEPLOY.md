# A8 部署草图（SaaS / 私有化）

## 参考拓扑

```
Client → Ingress → API (stateless Deployment)
                      ↓
              Queue / Outbox (Redis or PG SKIP LOCKED)
                      ↓
         Worker Deployment × N (lease consumer)
                      ↓
         Model Gateway  →  Upstream LLMs
                      ↓
         Postgres (checkpoint / ledger / audit) + PVC or managed PG
```

## K8s 要点

- API / Worker：`Deployment`，HPA 看队列深度（自定义指标），不是同步线程池扛长尾。
- PG：托管优先；自建需主从 + 备份；**单 PG = SPOF**。
- 模型网关：独立 Deployment；多供应商 fallback（见 A7）；**单供应商 = SPOF**。
- 审批队列：独立 topic；**单审批队列 = SPOF**。
- 多 AZ：Worker/API 打散；单区故障要能讲清降级与 RPO/RTO。

## 私有化差异

| 项 | 中心 SaaS | 私有化 |
|----|-----------|--------|
| PG | 托管多 AZ | 客户机房单机常见 → 必须文档化 SPOF |
| 模型 | 多供应商 | 常锁死内网单模型 → 网关仍要熔断 |
| 出网 | 可控 | 沙箱默认禁网（A5） |
| 升级 | 金丝雀（A6） | 蓝绿窗口短，holdout 门禁更重要 |

## 背压

租户隔离池 `max_inflight`；超限释放租约重入队，队列深度可观测。
