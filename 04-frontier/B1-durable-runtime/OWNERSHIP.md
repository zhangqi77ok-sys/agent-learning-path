# 网关 / MQ / Temporal Worker 归属（签字口径）

| 职责 | Spring 网关 | MQ | Temporal Worker | 禁止 |
|------|-------------|-----|-----------------|------|
| 抬权/内部令牌 | ✅ | 命令头复制身份 | 只信令牌+命令头 | Agent 直收用户 JWT 当权威 |
| 业务事务 | 领域服务 | 事件 | ❌ | Workflow 内开业务库事务 |
| HITL | 审批 UI | ApprovalGranted | Signal → Activity/Outbox | Signal 直接打款 |
| 超管 DB | — | — | ❌ | Worker 绕过领域 API |
