"""Durable SQLite store standing in for Postgres checkpointer + ledger + outbox + lease.

Production: swap DSN to Postgres; keep the same schemas and uniqueness constraints.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS checkpoints (
  tenant_id TEXT NOT NULL,
  thread_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  step INTEGER NOT NULL,
  status TEXT NOT NULL,
  payload TEXT NOT NULL,
  updated_ms REAL NOT NULL,
  PRIMARY KEY (tenant_id, thread_id, run_id)
);

CREATE TABLE IF NOT EXISTS effect_ledger (
  tenant_id TEXT NOT NULL,
  thread_id TEXT NOT NULL,
  effect_key TEXT NOT NULL,
  status TEXT NOT NULL, -- started | succeeded | unknown | compensated
  external_ref TEXT,
  updated_ms REAL NOT NULL,
  PRIMARY KEY (tenant_id, thread_id, effect_key)
);

CREATE TABLE IF NOT EXISTS outbox (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id TEXT NOT NULL,
  thread_id TEXT NOT NULL,
  effect_key TEXT NOT NULL,
  body TEXT NOT NULL,
  status TEXT NOT NULL, -- pending | dispatched | failed
  updated_ms REAL NOT NULL,
  UNIQUE (tenant_id, thread_id, effect_key)
);

CREATE TABLE IF NOT EXISTS leases (
  run_id TEXT PRIMARY KEY,
  worker_id TEXT NOT NULL,
  expires_ms REAL NOT NULL
);
"""


class Store:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def save_checkpoint(self, tenant_id: str, thread_id: str, run_id: str, step: int, status: str, payload: str) -> None:
        self.conn.execute(
            """
            INSERT INTO checkpoints(tenant_id, thread_id, run_id, step, status, payload, updated_ms)
            VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(tenant_id, thread_id, run_id) DO UPDATE SET
              step=excluded.step, status=excluded.status, payload=excluded.payload, updated_ms=excluded.updated_ms
            """,
            (tenant_id, thread_id, run_id, step, status, payload, time.time() * 1000),
        )
        self.conn.commit()

    def load_checkpoint(self, tenant_id: str, thread_id: str, run_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM checkpoints WHERE tenant_id=? AND thread_id=? AND run_id=?",
            (tenant_id, thread_id, run_id),
        ).fetchone()
        return dict(row) if row else None

    def begin_effect(self, tenant_id: str, thread_id: str, effect_key: str) -> str:
        """Return existing status if present, else insert 'started'."""
        row = self.conn.execute(
            "SELECT status FROM effect_ledger WHERE tenant_id=? AND thread_id=? AND effect_key=?",
            (tenant_id, thread_id, effect_key),
        ).fetchone()
        if row:
            return row["status"]
        self.conn.execute(
            "INSERT INTO effect_ledger(tenant_id, thread_id, effect_key, status, updated_ms) VALUES(?,?,?,?,?)",
            (tenant_id, thread_id, effect_key, "started", time.time() * 1000),
        )
        self.conn.commit()
        return "started"

    def complete_effect(self, tenant_id: str, thread_id: str, effect_key: str, external_ref: str, status: str = "succeeded") -> None:
        self.conn.execute(
            """
            UPDATE effect_ledger SET status=?, external_ref=?, updated_ms=?
            WHERE tenant_id=? AND thread_id=? AND effect_key=?
            """,
            (status, external_ref, time.time() * 1000, tenant_id, thread_id, effect_key),
        )
        self.conn.commit()

    def enqueue_outbox(self, tenant_id: str, thread_id: str, effect_key: str, body: str) -> None:
        self.conn.execute(
            """
            INSERT OR IGNORE INTO outbox(tenant_id, thread_id, effect_key, body, status, updated_ms)
            VALUES(?,?,?,?, 'pending', ?)
            """,
            (tenant_id, thread_id, effect_key, body, time.time() * 1000),
        )
        self.conn.commit()

    def dispatch_outbox_once(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM outbox WHERE status='pending' ORDER BY id").fetchall()
        dispatched = []
        for row in rows:
            self.conn.execute(
                "UPDATE outbox SET status='dispatched', updated_ms=? WHERE id=?",
                (time.time() * 1000, row["id"]),
            )
            dispatched.append(dict(row))
        self.conn.commit()
        return dispatched

    def try_acquire_lease(self, run_id: str, worker_id: str, ttl_ms: float = 5000) -> bool:
        now = time.time() * 1000
        row = self.conn.execute("SELECT * FROM leases WHERE run_id=?", (run_id,)).fetchone()
        if row and row["expires_ms"] > now and row["worker_id"] != worker_id:
            return False
        self.conn.execute(
            """
            INSERT INTO leases(run_id, worker_id, expires_ms) VALUES(?,?,?)
            ON CONFLICT(run_id) DO UPDATE SET worker_id=excluded.worker_id, expires_ms=excluded.expires_ms
            """,
            (run_id, worker_id, now + ttl_ms),
        )
        self.conn.commit()
        return True

    def release_lease(self, run_id: str, worker_id: str) -> None:
        self.conn.execute("DELETE FROM leases WHERE run_id=? AND worker_id=?", (run_id, worker_id))
        self.conn.commit()
