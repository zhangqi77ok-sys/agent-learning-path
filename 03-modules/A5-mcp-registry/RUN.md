# A5 RUN evidence

=== demo1: happy path ===
wrote /tmp/tmpijcr547h/sbx/notes/a.txt
=== demo2: description tamper (tool poisoning) ===
blocked: description_tamper
=== demo3: schema silent change (extra field) ===
blocked: schema_fingerprint_mismatch
SLO_ok_unreviewed_schema_block: True
=== demo4: sandbox escape ===
blocked: sandbox_escape
SLO_ok_sandbox_escape_0: True
=== demo5: tenant not allowlisted ===
blocked: tenant_not_allowlisted
=== demo6: unreviewed register fail-closed ===
blocked: unreviewed_tool
ALL_OK

