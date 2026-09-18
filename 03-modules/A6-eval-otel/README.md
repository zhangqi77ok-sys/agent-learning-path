# A6 · 四层 Eval + OTEL + 门禁

对照课纲 A6、口试 O6/O8、深挖 Q12–Q14。

## 硬规则

- 四层：Model / Framework / Harness / Application；硬门禁一票否决，软分数只作参考。
- 版本三元组：`eval_set × agent_config × model`。
- holdout 锁定，禁止写入 few-shot。
- Trace → fixture 必须脱敏；`retrieve` 缺 `filter` 标 incomplete。

## 运行

```bash
cd 03-modules/A6-eval-otel
python demo.py
```
