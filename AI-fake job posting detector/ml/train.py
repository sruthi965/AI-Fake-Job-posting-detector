"""Train and compare the classifiers, then save the best one.

    python -m ml.train --data data/fake_job_postings.csv

Outputs (in artifacts/):
    model.joblib    the selected pipeline, loaded by the API
    metrics.json    metrics for both models and the confusion matrix, shown on the dashboard
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.core.config import BASE_DIR
from app.models.prediction_model import build_bundle
from ml.evaluate import compute_metrics, confusion
from ml.preprocessing import load_dataset, split_data


def make_pipelines(seed: int) -> dict[str, Pipeline]:
    def tfidf() -> TfidfVectorizer:
        return TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=50000, sublinear_tf=True, stop_words="english")

    return {
        "logistic_regression": Pipeline([
            ("tfidf", tfidf()),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed)),
        ]),
        "random_forest": Pipeline([
            ("tfidf", tfidf()),
            ("clf", RandomForestClassifier(n_estimators=300, class_weight="balanced_subsample", n_jobs=-1, random_state=seed)),
        ]),
    }


def resolve(path: str) -> Path:
    return Path(path) if Path(path).is_absolute() else BASE_DIR / path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the fake job posting classifier.")
    parser.add_argument("--data", default="data/fake_job_postings.csv")
    parser.add_argument("--out", default="artifacts")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    data_path = resolve(args.data)
    if not data_path.exists():
        raise SystemExit(
            f"Dataset not found: {data_path}\n"
            "Download the 'Fake Job Postings' CSV (see data/README.md) or create a synthetic demo file with:\n"
            "    python -m ml.generate_sample_data"
        )

    df = load_dataset(data_path)
    x_train, x_test, y_train, y_test = split_data(df, args.test_size, args.seed)
    fraud_rate = float(df["label"].mean())
    print(f"{len(df)} unique postings, {fraud_rate:.1%} fraudulent; training on {len(x_train)}, testing on {len(x_test)}")

    results, fitted = {}, {}
    for name, pipeline in make_pipelines(args.seed).items():
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        results[name] = compute_metrics(y_test, predictions)
        fitted[name] = (pipeline, predictions)
        print(f"{name:20s} " + "  ".join(f"{k}={v:.3f}" for k, v in results[name].items()))

    best = max(results, key=lambda n: (results[n]["f1"], results[n]["recall"]))
    pipeline, predictions = fitted[best]
    out_dir = resolve(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    bundle = build_bundle(pipeline, best)
    joblib.dump(bundle, out_dir / "model.joblib")
    metrics = {
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset": {
            "source": data_path.name,
            "rows": int(len(df)),
            "fraud_rate": round(fraud_rate, 4),
            "test_rows": int(len(y_test)),
            "synthetic": bool(df["synthetic"].max()),
        },
        "selected_model": best,
        "models": results,
        "confusion_matrix": confusion(y_test, predictions),
    }
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Selected {best}. Saved model.joblib and metrics.json to {out_dir}")


if __name__ == "__main__":
    main()
