# A7 过关题作答（Q9 / Q10）

## 主模型 429 怎么办？

分类可重试错误 → 抖动/熔断 → fallback；决策写入 Trace；15s 内成功或 terminal_failure。

## 为什么缓存要带 tenant 和权限版本？

同 query 跨租户若共用缓存会串答泄密；ACL 变更后旧答案可能越权，故 `acl_version` 进 key。
