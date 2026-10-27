"""Shape of the model file saved by ``ml/train.py`` and loaded by the API."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypedDict


class ModelBundle(TypedDict):
    pipeline: Any  # scikit-learn Pipeline: TF-IDF vectoriser + classifier
    name: str
    trained_at: str
    threshold: float
    sklearn_version: str


def build_bundle(pipeline: Any, name: str, threshold: float = 0.5) -> ModelBundle:
    import sklearn

    return {
        "pipeline": pipeline,
        "name": name,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "threshold": threshold,
        "sklearn_version": sklearn.__version__,
    }
