import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import Settings


class Storage:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.path = self._resolve_path(settings)

    def initialize(self) -> None:
        if not self.settings.storage_enabled:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS emails (
                    address TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    email TEXT,
                    sender TEXT,
                    subject TEXT,
                    time TEXT,
                    preview TEXT,
                    text TEXT,
                    html TEXT,
                    updated_at TEXT NOT NULL
                );
                """
            )

    def record_event(self, event_type: str, payload: dict[str, Any]) -> None:
        if not self.settings.storage_enabled:
            return
        now = self._now()
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO events (event_type, payload, created_at) VALUES (?, ?, ?)",
                (event_type, json.dumps(payload, ensure_ascii=False), now),
            )

    def record_email(self, address: str, source: str = "tempail.com") -> None:
        if not self.settings.storage_enabled:
            return
        now = self._now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO emails (address, source, first_seen_at, last_seen_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(address) DO UPDATE SET last_seen_at = excluded.last_seen_at
                """,
                (address, source, now, now),
            )
        self.record_event("email_loaded", {"email": address})

    def record_messages(self, email: str | None, messages: list[Any]) -> None:
        if not self.settings.storage_enabled:
            return
        now = self._now()
        with self._connect() as connection:
            for message in messages:
                connection.execute(
                    """
                    INSERT INTO messages (id, email, sender, subject, time, preview, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        email = excluded.email,
                        sender = excluded.sender,
                        subject = excluded.subject,
                        time = excluded.time,
                        preview = excluded.preview,
                        updated_at = excluded.updated_at
                    """,
                    (
                        message.id,
                        email,
                        message.sender,
                        message.subject,
                        message.time,
                        message.preview,
                        now,
                    ),
                )
        self.record_event("inbox_loaded", {"email": email, "count": len(messages)})

    def record_content(self, content: Any) -> None:
        if not self.settings.storage_enabled:
            return
        now = self._now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO messages (id, sender, subject, time, text, html, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    sender = COALESCE(excluded.sender, messages.sender),
                    subject = COALESCE(excluded.subject, messages.subject),
                    time = COALESCE(excluded.time, messages.time),
                    text = excluded.text,
                    html = excluded.html,
                    updated_at = excluded.updated_at
                """,
                (content.id, content.sender, content.subject, content.time, content.text, content.html, now),
            )
        self.record_event("content_loaded", {"id": content.id, "subject": content.subject})

    def history(self, limit: int = 25) -> dict[str, Any]:
        if not self.settings.storage_enabled:
            return {"database_path": None, "emails": [], "messages": [], "events": []}
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            emails = connection.execute(
                "SELECT address, source, first_seen_at, last_seen_at FROM emails ORDER BY last_seen_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            messages = connection.execute(
                """
                SELECT id, email, sender, subject, time, preview, updated_at
                FROM messages
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            events = connection.execute(
                "SELECT event_type, payload, created_at FROM events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return {
            "database_path": str(self.path),
            "emails": [dict(row) for row in emails],
            "messages": [dict(row) for row in messages],
            "events": [self._event_dict(row) for row in events],
        }

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.path)

    def _resolve_path(self, settings: Settings) -> Path:
        if settings.database_path:
            return Path(settings.database_path)
        railway_mount = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
        data_dir = Path(railway_mount or settings.data_dir)
        return data_dir / "tempail.sqlite3"

    def _event_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "event_type": row["event_type"],
            "payload": json.loads(row["payload"]),
            "created_at": row["created_at"],
        }

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
