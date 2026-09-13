# A8 · 高可用 / 分布式 Agent 平台

对照课纲 A8、口试 O9、系统题 G1。

## 硬规则

- 长尾请求：队列 + 租约，不靠同步线程池。
- 多 Worker 抢队列；租户隔离池 + 背压。
- 能指出 SPOF：单 PG / 单模型供应商 / 单审批队列 / 单区。

## 运行

```bash
cd curriculum/advanced/A8-ha-platform
python demo.py
```

部署说明见 [DEPLOY.md](DEPLOY.md)。
