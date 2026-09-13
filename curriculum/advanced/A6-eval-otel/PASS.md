# A6 过关题作答（O6 / O8）

## 线下分涨了能不能发？

不能只看软分数。危险工具误开、缺 tenant filter、成本超预算、holdout 回退 ≥2pt → 硬门禁 veto。

## Bad Case 怎么进回归？

线上 Trace 经 `trace_to_fixture` 脱敏后入库；下一轮 CI 必跑。缺 `retrieve.filter` 的 trace 标 incomplete，不能当金标。
