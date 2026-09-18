# B1 过关口述

## checkpoint 数据 ≠ 运行时续跑

LangGraph/自研 checkpoint 恢复的是状态数据；Temporal Workflow 历史恢复的是**编排续跑**。副作用仍靠 Activity 幂等 + 领域 API。

## Signal 后为什么还要 Outbox/Activity？

Signal 可重复投递；Worker 可在 Signal 后崩溃。批准 → Activity(幂等键) → Java API，才是 exactly-once 外壳。

## 三项 Java 挂科

1. Workflow 当业务事务  
2. Signal 里直接打款  
3. Worker 持业务库超管账号绕过领域 API  
