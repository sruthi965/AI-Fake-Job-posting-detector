"""Dataset loading and splitting for model training."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from app.services.preprocessing import build_text, clean_text  # noqa: F401  (re-exported)

REQUIRED = {"title", "description", "fraudulent"}


def load_dataset(path: str | Path) -> pd.DataFrame:
    """Load a CSV and return a frame with ``text`` and ``label`` columns.

    Understands the public "Fake Job Postings" (EMSCAD) layout and the synthetic file produced
    by ``ml/generate_sample_data.py``.
    """
    df = pd.read_csv(path).fillna("")
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")

    if "company_name" not in df.columns:
        # EMSCAD has a company_profile text rather than a name; use presence as the signal.
        profile = df["company_profile"] if "company_profile" in df.columns else pd.Series([""] * len(df))
        df["company_name"] = profile.map(lambda v: "provided" if str(v).strip() else "")
    for column in ("requirements", "employment_type", "salary_range"):
        if column not in df.columns:
            df[column] = ""

    records = df.rename(columns={"title": "job_title"}).to_dict("records")
    out = pd.DataFrame(
        {
            "text": [build_text(r) for r in records],
            "label": df["fraudulent"].astype(int).values,
            "synthetic": int(df["synthetic"].max()) if "synthetic" in df.columns else 0,
        }
    )
    out = out[out["text"].str.len() > 0].drop_duplicates(subset="text").reset_index(drop=True)
    return out


def split_data(df: pd.DataFrame, test_size: float = 0.2, seed: int = 42):
    return train_test_split(
        df["text"], df["label"], test_size=test_size, random_state=seed, stratify=df["label"]
    )
