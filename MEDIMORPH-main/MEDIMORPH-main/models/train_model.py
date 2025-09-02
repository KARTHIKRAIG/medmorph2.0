import argparse
import json
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import StratifiedShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor


@dataclass
class TrainConfig:
    input_csv: str
    target: str
    features: Optional[List[str]]
    task: str  # "auto" | "classification" | "regression"
    model: str  # for classification: logreg|rf; for regression: ridge|rf
    test_size: float
    random_state: int
    output_dir: str


def infer_task(y: pd.Series) -> str:
    """
    Infer learning task from target series.
    - If dtype is numeric and unique values are many -> regression
    - If dtype is object/category or few unique values -> classification
    """
    if pd.api.types.is_numeric_dtype(y):
        # Heuristic: <= 20 unique numeric values -> likely classification
        return "classification" if y.nunique(dropna=True) <= 20 else "regression"
    return "classification"


def build_preprocessor(X: pd.DataFrame) -> Tuple[ColumnTransformer, List[str], List[str]]:
    numeric_features = [c for c in X.columns if pd.api.types.is_numeric_dtype(X[c])]
    categorical_features = [c for c in X.columns if c not in numeric_features]

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler(with_mean=False)),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ]
    )

    return preprocessor, numeric_features, categorical_features


def build_model(task: str, model_name: str):
    if task == "classification":
        if model_name == "logreg":
            return LogisticRegression(max_iter=200, n_jobs=None)
        if model_name == "rf":
            return RandomForestClassifier(n_estimators=300, random_state=42)
        raise ValueError(f"Unsupported classification model: {model_name}")
    else:
        if model_name == "ridge":
            return Ridge(random_state=42)
        if model_name == "rf":
            return RandomForestRegressor(n_estimators=300, random_state=42)
        raise ValueError(f"Unsupported regression model: {model_name}")


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


def stratified_split_if_possible(X: pd.DataFrame, y: pd.Series, test_size: float, random_state: int):
    try:
        splitter = StratifiedShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
        idx_train, idx_test = next(splitter.split(X, y))
        return (
            X.iloc[idx_train].reset_index(drop=True),
            X.iloc[idx_test].reset_index(drop=True),
            y.iloc[idx_train].reset_index(drop=True),
            y.iloc[idx_test].reset_index(drop=True),
        )
    except Exception:
        return train_test_split(X, y, test_size=test_size, random_state=random_state)


def train(cfg: TrainConfig) -> None:
    os.makedirs(cfg.output_dir, exist_ok=True)

    df = pd.read_csv(cfg.input_csv)
    if cfg.target not in df.columns:
        raise ValueError(f"Target column '{cfg.target}' not found in CSV.")

    feature_cols = cfg.features if cfg.features else [c for c in df.columns if c != cfg.target]
    X = df[feature_cols].copy()
    y = df[cfg.target].copy()

    task = cfg.task if cfg.task != "auto" else infer_task(y)

    preprocessor, num_cols, cat_cols = build_preprocessor(X)

    model = build_model(task, cfg.model)

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )

    # Split
    if task == "classification":
        X_train, X_test, y_train, y_test = stratified_split_if_possible(X, y, cfg.test_size, cfg.random_state)
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=cfg.test_size, random_state=cfg.random_state
        )

    # Fit
    pipeline.fit(X_train, y_train)

    # Evaluate
    y_pred = pipeline.predict(X_test)
    metrics = compute_metrics(task, y_test, y_pred)

    # Persist artifacts
    joblib.dump(pipeline, os.path.join(cfg.output_dir, "model.joblib"))
    manifest = {
        "task": task,
        "target": cfg.target,
        "features": feature_cols,
        "numeric_features": num_cols,
        "categorical_features": cat_cols,
        "model": cfg.model,
        "test_size": cfg.test_size,
        "random_state": cfg.random_state,
    }
    with open(os.path.join(cfg.output_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    with open(os.path.join(cfg.output_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("Saved:")
    print(f"- model: {os.path.join(cfg.output_dir, 'model.joblib')}")
    print(f"- manifest: {os.path.join(cfg.output_dir, 'manifest.json')}")
    print(f"- metrics: {os.path.join(cfg.output_dir, 'metrics.json')}")


def parse_args() -> TrainConfig:
    parser = argparse.ArgumentParser(description="Train a classification/regression model on a CSV dataset.")
    parser.add_argument("--csv", dest="input_csv", required=True, help="Path to input CSV file")
    parser.add_argument("--target", required=True, help="Target column name")
    parser.add_argument(
        "--features",
        help="Comma-separated list of feature columns (default: all except target)",
    )
    parser.add_argument(
        "--task",
        choices=["auto", "classification", "regression"],
        default="auto",
        help="Learning task (default: auto)",
    )
    parser.add_argument(
        "--model",
        default="rf",
        help="Model to use. classification: logreg|rf; regression: ridge|rf (default: rf)",
    )
    parser.add_argument("--test-size", type=float, default=0.2, help="Test split size (default: 0.2)")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument(
        "--out",
        dest="output_dir",
        default="models/artifacts",
        help="Directory to save model and reports (default: models/artifacts)",
    )

    args = parser.parse_args()
    features = [c.strip() for c in args.features.split(",")] if args.features else None
    return TrainConfig(
        input_csv=args.input_csv,
        target=args.target,
        features=features,
        task=args.task,
        model=args.model,
        test_size=args.test_size,
        random_state=args.random_state,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    cfg = parse_args()
    train(cfg)



