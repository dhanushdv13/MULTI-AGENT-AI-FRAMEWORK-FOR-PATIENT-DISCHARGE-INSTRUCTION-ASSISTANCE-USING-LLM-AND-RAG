"""
SQLite-backed session store for persistent chat history.
Survives server restarts. Each user+session has its own message history.
Includes automatic summarization when context gets too long.
"""
import json
import sqlite3
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict

from app.config import settings

logger = logging.getLogger("sessions")

# Session DB path
_DB_PATH = Path(settings.DATA_DIR) / "chat_sessions.db"


def _get_conn() -> sqlite3.Connection:
    """Get a SQLite connection (creates DB + table on first call)."""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_session
        ON chat_messages(user_id, session_id, created_at)
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS session_summaries (
            user_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            summary TEXT NOT NULL,
            updated_at REAL NOT NULL,
            PRIMARY KEY (user_id, session_id)
        )
    """)
    conn.commit()
    return conn


def add_message(user_id: int, session_id: str, role: str, content: str):
    """Add a message to session history (persistent)."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO chat_messages (user_id, session_id, role, content, created_at) VALUES (?,?,?,?,?)",
            (user_id, session_id, role, content, time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def get_recent_messages(user_id: int, session_id: str, limit: int = 20) -> List[Dict]:
    """Get the most recent messages for a session."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT role, content FROM chat_messages WHERE user_id=? AND session_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, session_id, limit),
        ).fetchall()
        # Reverse so oldest first
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]
    finally:
        conn.close()


def get_message_count(user_id: int, session_id: str) -> int:
    """Count total messages in a session."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM chat_messages WHERE user_id=? AND session_id=?",
            (user_id, session_id),
        ).fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def get_session_summary(user_id: int, session_id: str) -> Optional[str]:
    """Get the stored summary for a session (if any)."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT summary FROM session_summaries WHERE user_id=? AND session_id=?",
            (user_id, session_id),
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def save_session_summary(user_id: int, session_id: str, summary: str):
    """Save or update the summary for a session."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO session_summaries (user_id, session_id, summary, updated_at) VALUES (?,?,?,?)",
            (user_id, session_id, summary, time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def clear_session(user_id: int, session_id: str):
    """Delete all messages and summary for a session."""
    conn = _get_conn()
    try:
        conn.execute(
            "DELETE FROM chat_messages WHERE user_id=? AND session_id=?",
            (user_id, session_id),
        )
        conn.execute(
            "DELETE FROM session_summaries WHERE user_id=? AND session_id=?",
            (user_id, session_id),
        )
        conn.commit()
    finally:
        conn.close()


def build_context(user_id: int, session_id: str, max_recent: int = 10) -> str:
    """
    Build conversation context string for the LLM.

    Strategy (summarization):
    - If there are > max_recent messages, include the stored summary + last N messages.
    - If no summary yet but > max_recent, just use last N messages.
    - This keeps context compact for long conversations.
    """
    summary = get_session_summary(user_id, session_id)
    recent = get_recent_messages(user_id, session_id, limit=max_recent)

    if not recent and not summary:
        return ""

    parts = []
    if summary:
        parts.append(f"[Conversation summary so far]: {summary}")
    for m in recent:
        role = m["role"].capitalize()
        # Truncate very long messages
        text = m["content"][:600]
        parts.append(f"{role}: {text}")

    return "\n".join(parts)


def maybe_summarize(user_id: int, session_id: str, trigger_count: int = 20):
    """
    If session has more than `trigger_count` messages, summarize the older ones
    using the LLM and store the summary. Keeps context window manageable.

    This runs asynchronously after the response is sent.
    """
    count = get_message_count(user_id, session_id)
    if count < trigger_count:
        return  # Not enough messages to summarize

    logger.info("[Sessions] Session has %d messages, triggering summarization...", count)

    # Get all messages (not just recent)
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT role, content FROM chat_messages WHERE user_id=? AND session_id=? ORDER BY created_at",
            (user_id, session_id),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return

    # Build the conversation text (truncate each message)
    messages_text = "\n".join(
        f"{r[0].capitalize()}: {r[1][:300]}" for r in rows[:-10]  # Summarize all except last 10
    )

    existing_summary = get_session_summary(user_id, session_id) or ""

    try:
        from app.agents.base import get_llm
        llm = get_llm(temperature=0.3)

        prompt = f"""Summarize the following conversation history into a concise paragraph.
Preserve key facts: patient conditions, medications discussed, bill issues found,
diet recommendations given, and any important decisions or conclusions.

{f"Previous summary: {existing_summary}" if existing_summary else ""}

Conversation to summarize:
{messages_text}

Concise summary (2-4 sentences):"""

        response = llm.invoke(prompt)
        summary = response.content.strip()

        if summary:
            save_session_summary(user_id, session_id, summary)
            logger.info("[Sessions] Summary saved (%d chars)", len(summary))

            # Delete old messages (keep only last 10)
            conn = _get_conn()
            try:
                # Get the timestamp of the 10th most recent message
                cutoff_row = conn.execute(
                    "SELECT created_at FROM chat_messages WHERE user_id=? AND session_id=? ORDER BY created_at DESC LIMIT 1 OFFSET 9",
                    (user_id, session_id),
                ).fetchone()
                if cutoff_row:
                    conn.execute(
                        "DELETE FROM chat_messages WHERE user_id=? AND session_id=? AND created_at < ?",
                        (user_id, session_id, cutoff_row[0]),
                    )
                    conn.commit()
                    logger.info("[Sessions] Pruned old messages")
            finally:
                conn.close()

    except Exception as e:
        logger.error("[Sessions] Summarization failed: %s", e)
