import argparse
import json
import os
from typing import Optional, List

import joblib
import pandas as pd


def load_manifest(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def predict(
    model_path: str,
    manifest_path: str,
    csv_path: str,
    features: Optional[List[str]],
    output_csv: Optional[str],
    id_column: Optional[str],
    proba: bool,
):
    pipeline = joblib.load(model_path)
    manifest = load_manifest(manifest_path)

    df = pd.read_csv(csv_path)

    feat_cols = features or manifest.get("features")
    if not feat_cols:
        feat_cols = [c for c in df.columns]

    X = df[feat_cols].copy()

    if proba and hasattr(pipeline, "predict_proba"):
        preds = pipeline.predict_proba(X)
        pred_df = pd.DataFrame(preds, columns=[f"proba_{i}" for i in range(preds.shape[1])])
    else:
        preds = pipeline.predict(X)
        pred_df = pd.DataFrame({"prediction": preds})

    if id_column and id_column in df.columns:
        pred_df.insert(0, id_column, df[id_column].values)

    if output_csv:
        os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
        pred_df.to_csv(output_csv, index=False)
        print(f"Saved predictions to: {output_csv}")
    else:
        print(pred_df.head(20).to_string(index=False))


def parse_args():
    parser = argparse.ArgumentParser(description="Generate predictions from a trained model.")
    parser.add_argument("--model", required=True, help="Path to model.joblib")
    parser.add_argument("--manifest", required=True, help="Path to manifest.json")
    parser.add_argument("--csv", required=True, help="Path to input CSV for prediction")
    parser.add_argument("--features", help="Comma-separated feature columns (optional; defaults to manifest)")
    parser.add_argument("--out", dest="output_csv", help="Optional output CSV path for predictions")
    parser.add_argument("--id", dest="id_column", help="Optional ID column to include in output")
    parser.add_argument("--proba", action="store_true", help="Output class probabilities when supported")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    features = [c.strip() for c in args.features.split(",")] if args.features else None
    predict(
        model_path=args.model,
        manifest_path=args.manifest,
        csv_path=args.csv,
        features=features,
        output_csv=args.output_csv,
        id_column=args.id_column,
        proba=args.proba,
    )



