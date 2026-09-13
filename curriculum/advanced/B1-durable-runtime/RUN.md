# B1 RUN evidence

=== demo1: Signal → Outbox/Activity → ticket (no business tx in Workflow) ===
ref: TCK-1 create_calls: 1
SLO_ok_signal_then_activity: True
=== demo2: duplicate Signal → still exactly one ticket ===
ref: TCK-1 create_calls: 1
SLO_ok_duplicate_signal_exactly_once: True
=== demo3: await approval survives (query) + idempotent key ===
crash_resume_ticket: TCK-1 unique_tickets: 1
SLO_ok_durable_wait_and_idempotency: True
=== demo4 hangup: Worker superuser DB bypass (must fail closed) ===
blocked_as_expected: WorkflowFailureError Workflow execution failed
SLO_ok_no_superuser_bypass: True
=== ownership oral ===
gateway: auth/elevation | MQ: commands | temporal: orchestration | java domain: money tx
ALL_OK

