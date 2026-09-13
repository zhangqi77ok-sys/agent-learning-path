# A2 过关题作答（Q4–Q6 / O1–O3）

## O1. 工具已成功但 checkpoint 写失败？

不能盲 retry。流程：ledger `started` → 外部调用 → 先记 `unknown`+`external_ref`+outbox → 再标 `succeeded` 并写 checkpoint。  
崩溃后 resume：若 ledger 已有 `external_ref`，**禁止再调外部**，只做对账到 `succeeded`。

## O2. Rollback 撤不掉已付款/已发信？

状态回滚 ≠ 外部副作用回滚。需要补偿/Saga 或人工；ledger 保留证据。

## O3 / 租约

长任务靠耐久 checkpoint + lease；双 Worker 时只有持有 lease 的执行。取消写入状态并在下一步生效。
