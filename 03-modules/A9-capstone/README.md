# A9 Capstone · 多租户企业 Agent 控制面

作品集**唯一主项目**：Java 鉴权 → Python Harness → 检索/工具/HITL → Outbox → Trace → Eval。

## 五段演示

| ID | 内容 | 最低证据 |
|----|------|----------|
| (a) | 四隔离键 + 跨租户 checkpoint=0 | `demo.py` 段 a |
| (b) | 已批准副作用幂等 + Outbox | 重复 resume → external mock=1 |
| (c) | 检索 ACL | 跨租户不串答 |
| (d) | Loop 预算与熔断 | `circuit_open` / `policy_blocked` |
| (e) | Trace→Bad Case→Eval | 脱敏 fixture；incomplete 禁入库 |

## 运行

```bash
cd 03-modules/A9-capstone
python demo.py
python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
PYTHONPATH=. .venv/bin/python -m pytest tests/ -q
```

## P95 声明

本 Capstone 演示用进程内 mock；接入中转站时只读问答 P95 目标 `<8s`（依赖网络与模型，需在实测环境重测）。

## 10 个死亡坑对照

见 [HOLES.md](HOLES.md)。
