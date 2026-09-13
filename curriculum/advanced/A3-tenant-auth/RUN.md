# A3 跑通证据

日期：2026-09-13  
命令：`python demo.py`

```text
cross-tenant: A→[A1] B→[B1]  SLO_ok_no_cross_tenant: True
role ACL: alice 看不到 A2；admin 看得到 A2
bypass/no token → missing_internal_token
tampered token → bad_signature
approval expired → side_effects=[]
approve in time → exported
non-approver → role_not_allowed
```
