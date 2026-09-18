# A2 过关题作答（Q4–Q6 / O1–O3）

## O1. 工具已成功但 checkpoint / ledger 未落稳？

**禁止**对 `started` 且无 `external_ref` 做裸重试。

标准路径：

1. 幂等键固定为业务意图：`tenant:thread:effect_key`（不是每次 attempt 新 UUID）
2. resume 时若本地无 ref：先 `find_by_idempotency_key` 对端；没有再 `create` **并带同一 Idempotency-Key**
3. 远端按 key 去重，保证业务实体只有一份；本地再写入 `unknown/succeeded` + outbox

故障注入两条都要过：

- 远端已成功、本地仍 `started` 无 ref → resume 不产生第二张票
- 本地已有 `unknown+ref` 后崩溃 → resume 只对账，不再调创建

## O2. Rollback 撤不掉已付款/已发信？

状态回滚 ≠ 外部副作用回滚；要补偿/Saga 或人工，ledger 留证据。

## O3 / 租约

耐久 checkpoint + worker lease；双 Worker 后者 `lease_denied`；cancel 写入状态。
