import argparse
import json
import os
from typing import Optional, List

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


def load_manifest(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_metrics(task: str, y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    if task == "classification":
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "f1_macro": float(f1_score(y_true, y_pred, average="macro")),
            "report": classification_report(y_true, y_pred, output_dict=True),
        }
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
    }


def evaluate(model_path: str, manifest_path: str, csv_path: str, target: Optional[str], features: Optional[List[str]]):
    pipeline = joblib.load(model_path)
    manifest = load_manifest(manifest_path)

    df = pd.read_csv(csv_path)

    tgt_col = target or manifest.get("target")
    if not tgt_col or tgt_col not in df.columns:
        raise ValueError("Target column not provided or not found in CSV.")

    feat_cols = features or manifest.get("features")
    if not feat_cols:
        feat_cols = [c for c in df.columns if c != tgt_col]

    X = df[feat_cols].copy()
    y = df[tgt_col].copy()

    y_pred = pipeline.predict(X)
    task = manifest.get("task", "classification")
    metrics = compute_metrics(task, y, y_pred)

    print(json.dumps(metrics, indent=2))


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate a trained model on a CSV dataset.")
    parser.add_argument("--model", required=True, help="Path to model.joblib")
    parser.add_argument("--manifest", required=True, help="Path to manifest.json")
    parser.add_argument("--csv", required=True, help="Path to evaluation CSV")
    parser.add_argument("--target", help="Target column (optional; defaults to manifest target)")
    parser.add_argument("--features", help="Comma-separated feature columns (optional; defaults to manifest)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    features = [c.strip() for c in args.features.split(",")] if args.features else None
    evaluate(
        model_path=args.model,
        manifest_path=args.manifest,
        csv_path=args.csv,
        target=args.target,
        features=features,
    )



