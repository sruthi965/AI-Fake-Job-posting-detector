"""Evaluation helpers and a command-line report.

    python -m ml.evaluate --data data/fake_job_postings.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import joblib
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score

from app.core.config import BASE_DIR
from ml.preprocessing import load_dataset, split_data

LABELS = ["Legitimate", "Fraudulent"]


def compute_metrics(y_true, y_pred) -> dict:
    """Metrics for the fraudulent class (positive = 1). Accuracy alone misleads on imbalanced data."""
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
    }


def confusion(y_true, y_pred) -> dict:
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
    return {"labels": LABELS, "matrix": matrix}  # rows = actual, columns = predicted


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the saved model on the held-out split.")
    parser.add_argument("--data", default="data/fake_job_postings.csv")
    parser.add_argument("--model", default="artifacts/model.joblib")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    data_path = Path(args.data) if Path(args.data).is_absolute() else BASE_DIR / args.data
    model_path = Path(args.model) if Path(args.model).is_absolute() else BASE_DIR / args.model
    bundle = joblib.load(model_path)  # only load files you trained yourself
    _, x_test, _, y_test = split_data(load_dataset(data_path), args.test_size, args.seed)
    predictions = (bundle["pipeline"].predict_proba(x_test)[:, 1] >= bundle["threshold"]).astype(int)
    print(f"Model: {bundle['name']}  (trained {bundle['trained_at']})")
    print(classification_report(y_test, predictions, target_names=LABELS, zero_division=0))
    print("Confusion matrix (rows = actual, columns = predicted):")
    print(confusion(y_test, predictions)["matrix"])


if __name__ == "__main__":
    main()
