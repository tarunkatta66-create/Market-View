import os
import json
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from marketpulse.spark_jobs.daily_returns import run_daily_returns_spark
from marketpulse.features.technical_indicators import build_technical_features
from marketpulse.models.lstm_model import LSTMClassifier
from marketpulse.models.evaluate import evaluate_predictions
from marketpulse.storage.mongo_client import MongoStore

FEATURE_COLS = ["Ret1", "Ret5", "MA5", "MA20", "RSI14", "Vol20", "VolChange", "Sentiment"]


def prepare_training_data() -> pd.DataFrame:
    raw_path = os.path.join("data", "raw", "prices_daily.csv")
    if not os.path.exists(raw_path):
        from marketpulse.ingest.download_data import fetch_historical_daily
        fetch_historical_daily()

    daily_returns_df = run_daily_returns_spark(raw_path)
    df_feat = build_technical_features(daily_returns_df)

    # Merge news sentiment
    store = MongoStore()
    news_docs = store.get_records("news", limit=1000)
    sentiment_map = {}
    if news_docs:
        for doc in news_docs:
            date_str = str(doc.get("pubDate", ""))[:10]
            score = float(doc.get("sentiment_score", 0.0))
            sentiment_map[date_str] = sentiment_map.get(date_str, 0.0) + score

    df_feat["Sentiment"] = df_feat["Date"].map(lambda d: round(sentiment_map.get(str(d), 0.0), 3))
    df_feat = df_feat.sort_values(by="Date").reset_index(drop=True)
    return df_feat


def walk_forward_split(df: pd.DataFrame, n_splits: int = 3) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Expanding-window walk-forward split to prevent data leakage in time-series data.
    """
    unique_dates = sorted(df["Date"].unique())
    n_dates = len(unique_dates)
    if n_dates < 30:
        split_idx = int(n_dates * 0.7)
        train_dates = set(unique_dates[:split_idx])
        test_dates = set(unique_dates[split_idx:])
        return [(df[df["Date"].isin(train_dates)], df[df["Date"].isin(test_dates)])]

    splits = []
    step = (n_dates - 20) // n_splits
    for i in range(1, n_splits + 1):
        train_end_idx = 20 + i * step
        test_end_idx = min(n_dates, train_end_idx + step)
        
        train_d = set(unique_dates[:train_end_idx])
        test_d = set(unique_dates[train_end_idx:test_end_idx])
        
        if train_d and test_d:
            splits.append((df[df["Date"].isin(train_d)], df[df["Date"].isin(test_d)]))
    return splits


def train_and_evaluate_all() -> Dict[str, Any]:
    df = prepare_training_data()
    splits = walk_forward_split(df, n_splits=3)

    model_preds = {
        "logistic_regression": {"y_true": [], "y_pred": [], "y_prob": []},
        "random_forest": {"y_true": [], "y_pred": [], "y_prob": []},
        "lstm": {"y_true": [], "y_pred": [], "y_prob": []}
    }

    final_rf = None
    final_scaler = StandardScaler()

    for train_df, test_df in splits:
        if train_df.empty or test_df.empty:
            continue

        X_train = train_df[FEATURE_COLS].values
        y_train = train_df["Target_Up"].values
        X_test = test_df[FEATURE_COLS].values
        y_test = test_df["Target_Up"].values

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        # 1. Logistic Regression
        lr = LogisticRegression(random_state=42, max_iter=200)
        lr.fit(X_train_s, y_train)
        lr_pred = lr.predict(X_test_s)
        lr_prob = lr.predict_proba(X_test_s)[:, 1] if hasattr(lr, "predict_proba") else lr_pred

        model_preds["logistic_regression"]["y_true"].extend(y_test)
        model_preds["logistic_regression"]["y_pred"].extend(lr_pred)
        model_preds["logistic_regression"]["y_prob"].extend(lr_prob)

        # 2. Random Forest
        rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        rf.fit(X_train_s, y_train)
        rf_pred = rf.predict(X_test_s)
        rf_prob = rf.predict_proba(X_test_s)[:, 1]
        final_rf = rf
        final_scaler = scaler

        model_preds["random_forest"]["y_true"].extend(y_test)
        model_preds["random_forest"]["y_pred"].extend(rf_pred)
        model_preds["random_forest"]["y_prob"].extend(rf_prob)

        # 3. LSTM
        lstm = LSTMClassifier(input_dim=len(FEATURE_COLS))
        lstm.fit(X_train_s, y_train, epochs=15)
        lstm_pred = lstm.predict(X_test_s)
        lstm_prob = lstm.predict_proba(X_test_s)[:, 1]

        model_preds["lstm"]["y_true"].extend(y_test)
        model_preds["lstm"]["y_pred"].extend(lstm_pred)
        model_preds["lstm"]["y_prob"].extend(lstm_prob)

    metrics_result = {}
    for name, data in model_preds.items():
        metrics_result[name] = evaluate_predictions(
            np.array(data["y_true"]),
            np.array(data["y_pred"]),
            np.array(data["y_prob"])
        )

    # Save metrics JSON
    reports_dir = os.path.join("reports")
    os.makedirs(reports_dir, exist_ok=True)
    with open(os.path.join(reports_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics_result, f, indent=2)

    # Save trained RF model artifact
    models_dir = os.path.join("data", "processed")
    joblib.dump({"model": final_rf, "scaler": final_scaler}, os.path.join(models_dir, "rf_model.joblib"))

    # Generate test set predictions for MongoDB storage
    latest_test = splits[-1][1] if splits else df.tail(50)
    X_lat = final_scaler.transform(latest_test[FEATURE_COLS].values)
    preds = final_rf.predict(X_lat)
    probs = final_rf.predict_proba(X_lat)[:, 1]

    pred_records = []
    for idx, (_, row) in enumerate(latest_test.iterrows()):
        pred_records.append({
            "date": str(row["Date"]),
            "ticker": str(row["Ticker"]),
            "close": float(row["Close"]),
            "predicted_direction": "UP" if preds[idx] == 1 else "DOWN",
            "probability_up": round(float(probs[idx]), 3),
            "actual_direction": "UP" if row["Target_Up"] == 1 else "DOWN"
        })

    store = MongoStore()
    store.clear_collection("predictions")
    store.insert_records("predictions", pred_records)

    return metrics_result


if __name__ == "__main__":
    res = train_and_evaluate_all()
    print("Walk-forward training and evaluation complete. Results summary:")
    print(json.dumps(res, indent=2))
