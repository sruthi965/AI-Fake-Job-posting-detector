"""Text preparation shared by training (ml/) and inference (app/)."""
from __future__ import annotations

import html
import re

_TAGS = re.compile(r"<[^>]+>")
_URL = re.compile(r"(https?://\S+|www\.\S+)", re.I)
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(\.[\w-]+)+\b")
_MONEY = re.compile(r"[$€£₹]\s?\d[\d,]*(\.\d+)?\s?k?", re.I)
_NON_WORD = re.compile(r"[^a-z0-9_\s]")
_SPACES = re.compile(r"\s+")


def clean_text(text: str | None) -> str:
    """Lowercase, strip markup, and replace URLs, emails and amounts with stable tokens."""
    if not text:
        return ""
    text = html.unescape(str(text))
    text = _TAGS.sub(" ", text)
    text = _URL.sub(" urltoken ", text)
    text = _EMAIL.sub(" emailtoken ", text)
    text = _MONEY.sub(" moneytoken ", text)
    text = text.lower()
    text = _NON_WORD.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


def _flag(value: str | None, yes: str, no: str) -> str:
    return yes if value and str(value).strip() else no


def build_text(job: dict) -> str:
    """Combine the fields of a posting into the single string the classifier reads.

    The company name and salary text themselves are not included, only whether they were
    provided, so the model does not memorise specific names or number formats.
    """
    employment = re.sub(r"[^a-z0-9]", "", str(job.get("employment_type") or "").lower())
    parts = [
        job.get("job_title"),
        _flag(job.get("company_name"), "hascompany", "nocompany"),
        f"emp_{employment}" if employment else "emp_unknown",
        _flag(job.get("salary_range"), "hassalary", "nosalary"),
        job.get("description"),
        job.get("requirements"),
    ]
    return clean_text(" . ".join(str(p) for p in parts if p))
