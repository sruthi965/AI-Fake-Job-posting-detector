"""Data access functions. All SQL lives here and always uses bound parameters."""
from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.database.connection import execute, get_connection


def _normalize(row: Any) -> dict | None:
    if row is None:
        return None
    out = dict(row)
    for key, value in out.items():
        if isinstance(value, Decimal):
            out[key] = float(value)
        elif isinstance(value, datetime):
            out[key] = value.isoformat(sep=" ")
        elif isinstance(value, date):
            out[key] = value.isoformat()
    return out


def _load_json(value: Any, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _analysis(row: Any) -> dict | None:
    data = _normalize(row)
    if data is None:
        return None
    data["risk_indicators"] = _load_json(data.get("risk_indicators"), [])
    explanation = _load_json(data.get("explanation"), None)
    data["explanation"] = explanation if isinstance(explanation, dict) else None
    return data


# ---------------------------------------------------------------- users
def create_user(full_name: str, email: str, password_hash: str) -> int:
    with get_connection() as conn:
        cursor = execute(
            conn,
            "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
            (full_name, email, password_hash),
        )
        return int(cursor.lastrowid)


def get_user_by_email(email: str) -> dict | None:
    with get_connection() as conn:
        return _normalize(execute(conn, "SELECT * FROM users WHERE email = ?", (email,)).fetchone())


def get_user_by_id(user_id: int) -> dict | None:
    with get_connection() as conn:
        return _normalize(execute(conn, "SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())


# ------------------------------------------------------------- analyses
def save_analysis(user_id: int | None, data: dict) -> int:
    explanation = data.get("explanation")
    with get_connection() as conn:
        cursor = execute(
            conn,
            """INSERT INTO job_analysis
               (user_id, job_title, company_name, description, requirements, employment_type,
                salary_range, prediction, fraud_probability, risk_indicators, explanation, model_used)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                data["job_title"],
                data.get("company_name"),
                data["description"],
                data.get("requirements"),
                data.get("employment_type"),
                data.get("salary_range"),
                data["prediction"],
                round(float(data["fraud_probability"]), 2),
                json.dumps(data.get("risk_indicators") or []),
                json.dumps(explanation) if explanation else None,
                data.get("model_used"),
            ),
        )
        return int(cursor.lastrowid)


def list_analyses(user_id: int, page: int, page_size: int) -> tuple[list[dict], int]:
    offset = (page - 1) * page_size
    with get_connection() as conn:
        total = execute(conn, "SELECT COUNT(*) AS total FROM job_analysis WHERE user_id = ?", (user_id,)).fetchone()
        rows = execute(
            conn,
            """SELECT id, job_title, company_name, prediction, fraud_probability, created_at
               FROM job_analysis WHERE user_id = ? ORDER BY id DESC LIMIT ? OFFSET ?""",
            (user_id, page_size, offset),
        ).fetchall()
    return [_normalize(r) for r in rows], int(dict(total)["total"])


def get_analysis(analysis_id: int, user_id: int) -> dict | None:
    with get_connection() as conn:
        row = execute(
            conn, "SELECT * FROM job_analysis WHERE id = ? AND user_id = ?", (analysis_id, user_id)
        ).fetchone()
    return _analysis(row)


def update_explanation(analysis_id: int, user_id: int, explanation: dict) -> bool:
    with get_connection() as conn:
        cursor = execute(
            conn,
            "UPDATE job_analysis SET explanation = ? WHERE id = ? AND user_id = ?",
            (json.dumps(explanation), analysis_id, user_id),
        )
        return cursor.rowcount > 0


def delete_analysis(analysis_id: int, user_id: int) -> bool:
    with get_connection() as conn:
        cursor = execute(conn, "DELETE FROM job_analysis WHERE id = ? AND user_id = ?", (analysis_id, user_id))
        return cursor.rowcount > 0


def user_stats(user_id: int) -> dict:
    with get_connection() as conn:
        row = execute(
            conn,
            """SELECT COUNT(*) AS total,
                      SUM(CASE WHEN prediction = 'Fraudulent' THEN 1 ELSE 0 END) AS fraudulent,
                      AVG(fraud_probability) AS avg_probability
               FROM job_analysis WHERE user_id = ?""",
            (user_id,),
        ).fetchone()
    data = dict(row)
    total = int(data["total"] or 0)
    fraudulent = int(data["fraudulent"] or 0)
    return {
        "total_analyses": total,
        "fraudulent": fraudulent,
        "legitimate": total - fraudulent,
        "average_probability": round(float(data["avg_probability"] or 0), 1),
    }
