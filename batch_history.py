from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from batch_monitor_core import BatchResult


class BatchHistory:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS batches (
                    signature TEXT PRIMARY KEY,
                    observed_at REAL NOT NULL,
                    pay REAL NOT NULL,
                    distance REAL NOT NULL,
                    items INTEGER NOT NULL DEFAULT 0,
                    net_estimate REAL NOT NULL,
                    hourly_estimate REAL NOT NULL,
                    recommendation TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'offered'
                )
                """
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(batches)")}
            if "items" not in columns:
                connection.execute("ALTER TABLE batches ADD COLUMN items INTEGER NOT NULL DEFAULT 0")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def record(self, result: BatchResult) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO batches
                (signature, observed_at, pay, distance, items, net_estimate, hourly_estimate, recommendation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (result.signature, result.observed_at, result.pay, result.distance, result.items, result.net_estimate, result.hourly_estimate, result.recommendation),
            )

    def mark_latest(self, status: str) -> None:
        with self._connect() as connection:
            latest = connection.execute("SELECT signature FROM batches ORDER BY observed_at DESC LIMIT 1").fetchone()
        if latest:
            self.mark(latest[0], status)

    def mark(self, signature: str, status: str) -> None:
        if status not in {"completed", "skipped"}:
            raise ValueError("Unsupported batch status")
        with self._connect() as connection:
            connection.execute("UPDATE batches SET status = ? WHERE signature = ?", (status, signature))

    def recent(self, limit: int = 50) -> list[dict[str, object]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT signature, observed_at, pay, distance, items, net_estimate,
                       hourly_estimate, recommendation, status
                FROM batches ORDER BY observed_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "signature": row[0], "observed_at": row[1], "pay": row[2],
                "distance": row[3], "items": row[4], "net_estimate": row[5],
                "hourly_estimate": row[6], "recommendation": row[7], "status": row[8],
            }
            for row in rows
        ]

    def summary(self) -> dict[str, float]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*),
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END),
                    COALESCE(SUM(CASE WHEN status = 'completed' THEN pay ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN status = 'completed' THEN net_estimate ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN status = 'completed' THEN distance ELSE 0 END), 0),
                    COALESCE(AVG(CASE WHEN status = 'completed' THEN hourly_estimate END), 0)
                FROM batches
                """
            ).fetchone()
        return {
            "offers": float(row[0] or 0),
            "completed": float(row[1] or 0),
            "gross": float(row[2] or 0),
            "net": float(row[3] or 0),
            "distance": float(row[4] or 0),
            "average_hourly": float(row[5] or 0),
        }
