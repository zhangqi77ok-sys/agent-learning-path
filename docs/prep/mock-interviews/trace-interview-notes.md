# Trace 面试口径（旁注）

> 来源：群同步（架构 + 深挖）。配合 A6 / A9-e / 计时练习包。

## 是什么

一次请求 / 一次 Agent run 的全链路记录：每个步骤一个 **span**（模型、retrieve、tool、审批、Outbox、Java API…），带父子关系与统一属性。

## 架构口径

Trace **要能跨过** Gateway → Harness → Outbox → Java API。  
用它证明「谁写了外部世界」：例如 Signal 没有直打库；第二次 resume 命中同一 `external_ref`。  
若只有 Python 侧 span、断在 Java 入口，归属链讲不清。

## 深挖口径

面试官甩一段 Trace 时：

1. 先看 span **类型** → 映射 Model / Framework / Harness / Application  
2. 再决定改 Prompt 还是补门禁  

例：缺 `retrieve.filter` → **硬否决发版**，不是先换模型。

## 仓库证据

- `03-modules/A6-eval-otel/otel/trace_to_fixture.py`
- Capstone (e)：`03-modules/A9-capstone/`
- 假 Trace 排障：Mock R3 可选加时
