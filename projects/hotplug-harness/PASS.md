# 口述过关：Hot-plug Harness

## 热插拔 vs 硬编码

- **硬编码**：tools / model / policy 写死在核心循环里；加一个工具要改 `harness.py`、重新发版、容易把 ACL 和业务缠在一起。
- **热插拔**：核心只认 Protocol（`name` + `run` / `propose` / `check`）；`loader` 扫 `plugins/{tools,models,policies}/*.py`，注册进 `registry`。加工具 = 丢一个文件，**零核心 diff**。面试可以说：扩展面在插件边界，控制面（预算/白名单/熔断）仍集中在 Harness。

## Harness vs Model 所有权

- **Model**：只提出下一步（`final` 或 `tool_calls`）。它不知道、也不该绕过预算与策略。
- **Harness**：拥有 Loop；每一步先查 Budget，再跑 Policy（allowlist），再 Circuit（重复 signature），才执行 Tool；写 Event log，支持 Cancel / Replay。
- 一句话：`Model + Harness = Agent` —— 模型负责「想」，Harness 负责「能不能做、做多久、做错了怎么停」。

## 隔离键

每次 `start_run` 绑定 `tenant_id / user_id / thread_id / run_id`，事件账带上这些键，后续才能做租户级 Trace→Eval。
