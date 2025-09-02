# Model Training and Evaluation

This folder contains standalone scripts to train and evaluate a simple ML model on a CSV dataset. They are independent of the Flask app and can be used for documentation or experiments.

## Files
- `train_model.py`: Trains a model, saves artifacts (`model.joblib`, `manifest.json`, `metrics.json`).
- `evaluate_model.py`: Loads a saved model and evaluates it on a CSV file.
- `predict.py`: Generates predictions (labels or probabilities) for a CSV file.

## Install dependencies
Use the existing project virtual environment:

```bash
.\.venv\Scripts\python.exe -m pip install scikit-learn pandas joblib
```

(These may already be installed from `requirements.txt`.)

## Dataset format
- Input: CSV file.
- Provide a `--target` column to predict.
- By default, all other columns are used as features. Use `--features` to specify a subset.
- The task is inferred automatically: numeric target with many unique values → regression; otherwise classification. You can override with `--task`.

## Train
```bash
.\.venv\Scripts\python.exe models\train_model.py \
  --csv path\to\data.csv \
  --target label_column \
  --task auto \
  --model rf \
  --test-size 0.2 \
  --out models\artifacts
```

Artifacts saved to `models/artifacts/`:
- `model.joblib`: Preprocessing + estimator pipeline
- `manifest.json`: Metadata (task, features, target)
- `metrics.json`: Test metrics

## Evaluate
```bash
.\.venv\Scripts\python.exe models\evaluate_model.py \
  --model models\artifacts\model.joblib \
  --manifest models\artifacts\manifest.json \
  --csv path\to\eval.csv
```

Optional overrides: `--target`, `--features col1,col2,...`

## Predict (Classification or Regression)
```bash
.\.venv\Scripts\python.exe models\predict.py \
  --model models\artifacts\model.joblib \
  --manifest models\artifacts\manifest.json \
  --csv path\to\unlabeled.csv \
  --out models\artifacts\predictions.csv
```

Options:
- `--features col1,col2,...` to override feature columns
- `--id some_id_column` to include an ID in the output
- `--proba` to output class probabilities (if supported)

## Notes
- Classification models: `logreg` (Logistic Regression), `rf` (RandomForestClassifier).
- Regression models: `ridge` (Ridge), `rf` (RandomForestRegressor).
- Mixed numeric/categorical features are handled via a `ColumnTransformer` with imputation and scaling/one-hot encoding.


