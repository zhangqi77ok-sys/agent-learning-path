# A4 过关题作答

## O4 多租户 RAG 怎么证明不串库？

身份来自网关；`search(identity, …)` 无客户端 tenant 参数；过滤在打分前；跨租户/投毒文档负向测试 hit=0。

## O7 不停服更新且历史可复现？

双索引蓝绿 + `atomic_switch`；回答记录 `kb_alias` + `doc@version`；replay 仍 pin 旧 alias。

## 过期

`expires_at < as_of` 不进候选；`effective_from` 未到也不进。
