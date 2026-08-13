"""SQLite logger for interaction tracking and response versioning."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List


class InteractionLogger:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp_utc TEXT NOT NULL,
                    question TEXT NOT NULL,
                    normalized_question TEXT NOT NULL,
                    input_hash TEXT NOT NULL,
                    detected_intent TEXT NOT NULL,
                    response_version TEXT NOT NULL,
                    response_text TEXT NOT NULL,
                    response_time_ms REAL NOT NULL,
                    guardrail_triggered INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS response_versions (
                    intent TEXT NOT NULL,
                    version TEXT NOT NULL,
                    response_text TEXT NOT NULL,
                    PRIMARY KEY (intent, version)
                )
                """
            )

    def upsert_response_version(self, intent: str, version: str, response_text: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO response_versions(intent, version, response_text)
                VALUES (?, ?, ?)
                ON CONFLICT(intent, version) DO UPDATE SET response_text=excluded.response_text
                """,
                (intent, version, response_text),
            )

    def log_interaction(self, payload: Dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO interactions(
                    timestamp_utc,
                    question,
                    normalized_question,
                    input_hash,
                    detected_intent,
                    response_version,
                    response_text,
                    response_time_ms,
                    guardrail_triggered
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["timestamp_utc"],
                    payload["question"],
                    payload["normalized_question"],
                    payload["input_hash"],
                    payload["detected_intent"],
                    payload["response_version"],
                    payload["response_text"],
                    payload["response_time_ms"],
                    int(payload["guardrail_triggered"]),
                ),
            )

    def fetch_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT timestamp_utc, question, detected_intent, response_text, response_time_ms, guardrail_triggered
                FROM interactions
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "timestamp_utc": r[0],
                "question": r[1],
                "detected_intent": r[2],
                "response_text": r[3],
                "response_time_ms": r[4],
                "guardrail_triggered": bool(r[5]),
            }
            for r in rows
        ]
