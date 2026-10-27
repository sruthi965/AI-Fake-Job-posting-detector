"""Database access for MySQL (deployment) and SQLite (local development and tests).

Select the backend with DATABASE_URL:
    mysql://user:password@host:3306/dbname
    sqlite:///./jobguard.db
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import unquote, urlparse

from app.core.config import BASE_DIR, get_settings

SCHEMA_SQL_PATH = Path(__file__).with_name("schema.sql")

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS job_analysis (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    job_title         TEXT NOT NULL,
    company_name      TEXT,
    description       TEXT NOT NULL,
    requirements      TEXT,
    employment_type   TEXT,
    salary_range      TEXT,
    prediction        TEXT NOT NULL,
    fraud_probability REAL NOT NULL,
    risk_indicators   TEXT,
    explanation       TEXT,
    model_used        TEXT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id           INTEGER REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_job_analysis_user ON job_analysis (user_id, id);
"""


def is_sqlite() -> bool:
    return get_settings().database_url.startswith("sqlite")


def _sqlite_path(url: str) -> str:
    raw = url[len("sqlite:///"):]
    if raw == ":memory:":
        return raw
    path = Path(raw)
    if not path.is_absolute():
        path = BASE_DIR / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def integrity_errors() -> tuple[type[BaseException], ...]:
    errors: tuple[type[BaseException], ...] = (sqlite3.IntegrityError,)
    try:
        import pymysql

        errors += (pymysql.err.IntegrityError,)
    except ImportError:  # pragma: no cover - MySQL driver not installed
        pass
    return errors


@contextmanager
def get_connection() -> Iterator[Any]:
    """Yield a connection that commits on success and rolls back on error."""
    url = get_settings().database_url
    if url.startswith("sqlite"):
        conn = sqlite3.connect(_sqlite_path(url))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
    else:
        import pymysql

        parsed = urlparse(url)
        conn = pymysql.connect(
            host=parsed.hostname or "localhost",
            port=parsed.port or 3306,
            user=unquote(parsed.username or ""),
            password=unquote(parsed.password or ""),
            database=parsed.path.lstrip("/"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute(conn: Any, sql: str, params: tuple | list = ()) -> Any:
    """Run a statement written with ``?`` placeholders on either backend."""
    if not is_sqlite():
        sql = sql.replace("?", "%s")
    cursor = conn.cursor()
    cursor.execute(sql, tuple(params))
    return cursor


def init_db() -> None:
    """Create tables if they do not exist."""
    with get_connection() as conn:
        if is_sqlite():
            conn.executescript(SQLITE_SCHEMA)
            return
        lines = [ln for ln in SCHEMA_SQL_PATH.read_text(encoding="utf-8").splitlines() if not ln.strip().startswith("--")]
        for statement in "\n".join(lines).split(";"):
            if statement.strip():
                cursor = conn.cursor()
                cursor.execute(statement)


def check_connection() -> bool:
    try:
        with get_connection() as conn:
            execute(conn, "SELECT 1").fetchone()
        return True
    except Exception:
        return False
