"""SQLite stand-in for PG: checkpoints + effect ledger + outbox."""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path


class Store:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS checkpoints (
              tenant_id TEXT, thread_id TEXT, run_id TEXT, user_id TEXT,
              step INT, state_json TEXT,
              PRIMARY KEY (tenant_id, thread_id, run_id, step)
            );
            CREATE TABLE IF NOT EXISTS effect_ledger (
              tenant_id TEXT, thread_id TEXT, effect_key TEXT,
              idempotency_key TEXT UNIQUE,
              status TEXT, external_ref TEXT,
              PRIMARY KEY (tenant_id, thread_id, effect_key)
            );
            CREATE TABLE IF NOT EXISTS outbox (
              id TEXT PRIMARY KEY,
              tenant_id TEXT, thread_id TEXT, effect_key TEXT,
              payload_json TEXT, status TEXT, created_at REAL
            );
            """
        )
        self.conn.commit()

    def save_checkpoint(self, keys, step: int, state: dict) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO checkpoints VALUES (?,?,?,?,?,?)",
            (keys.tenant_id, keys.thread_id, keys.run_id, keys.user_id, step, json.dumps(state)),
        )
        self.conn.commit()

    def read_checkpoint(self, tenant_id: str, thread_id: str, run_id: str):
        cur = self.conn.execute(
            "SELECT * FROM checkpoints WHERE tenant_id=? AND thread_id=? AND run_id=? ORDER BY step DESC LIMIT 1",
            (tenant_id, thread_id, run_id),
        )
        return cur.fetchone()

    def cross_tenant_checkpoint_rows(self, attacker_tenant: str, thread_id: str, run_id: str) -> int:
        cur = self.conn.execute(
            "SELECT COUNT(*) AS c FROM checkpoints WHERE tenant_id=? AND thread_id=? AND run_id=?",
            (attacker_tenant, thread_id, run_id),
        )
        return int(cur.fetchone()["c"])

    def begin_effect(self, tenant_id: str, thread_id: str, effect_key: str) -> str:
        idem = f"{tenant_id}:{thread_id}:{effect_key}"
        self.conn.execute(
            "INSERT OR IGNORE INTO effect_ledger VALUES (?,?,?,?,?,?)",
            (tenant_id, thread_id, effect_key, idem, "started", None),
        )
        self.conn.commit()
        return idem

    def get_effect(self, idem: str):
        return self.conn.execute(
            "SELECT * FROM effect_ledger WHERE idempotency_key=?", (idem,)
        ).fetchone()

    def complete_effect(self, idem: str, external_ref: str) -> None:
        self.conn.execute(
            "UPDATE effect_ledger SET status='done', external_ref=? WHERE idempotency_key=?",
            (external_ref, idem),
        )
        self.conn.commit()

    def enqueue_outbox(self, tenant_id: str, thread_id: str, effect_key: str, payload: dict) -> str:
        oid = str(uuid.uuid4())[:8]
        self.conn.execute(
            "INSERT INTO outbox VALUES (?,?,?,?,?,?,?)",
            (oid, tenant_id, thread_id, effect_key, json.dumps(payload), "pending", time.time()),
        )
        self.conn.commit()
        return oid

    def pending_outbox(self):
        return self.conn.execute("SELECT * FROM outbox WHERE status='pending'").fetchall()

    def mark_outbox(self, oid: str, status: str) -> None:
        self.conn.execute("UPDATE outbox SET status=? WHERE id=?", (status, oid))
        self.conn.commit()
