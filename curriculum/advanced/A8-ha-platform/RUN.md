# A8 RUN evidence

=== demo1: two workers race-claim queue (no double process) ===
processed: 20 per_worker: [10, 10]
SLO_ok_dual_worker_exactly_once: True
=== demo2: noisy tenantA fills pool — tenantB P95 <= 2x baseline ===
baseline_B_p95_ms: 8.13
noisy_B_p95_ms: 8.15 rejected_A: 0
queue_depth_samples_max: 110
SLO_ok_tenant_isolation_p95: True
=== demo3: PG pause (SPOF) — enqueue fails, claim returns None ===
blocked enqueue: pg_unavailable
SLO_ok_pg_spof_visible: True
=== demo4: model gateway all 503 ===
job_error: gateway_503
SLO_ok_gateway_503_terminal: True
=== SPOF checklist (oral) ===
SPOF: single_pg
SPOF: single_model_vendor
SPOF: single_approval_queue
SPOF: single_az
ALL_OK

