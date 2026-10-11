import os
import json
import pandas as pd
from typing import Dict, Any


def analyze_dataset_characteristics() -> Dict[str, Any]:
    raw_dir = os.path.join("data", "raw")
    
    daily_path = os.path.join(raw_dir, "prices_daily.csv")
    minute_path = os.path.join(raw_dir, "prices_minute.csv")
    news_path = os.path.join(raw_dir, "news_headlines.json")

    daily_rows = 0
    daily_bytes = 0
    if os.path.exists(daily_path):
        df_daily = pd.read_csv(daily_path)
        daily_rows = len(df_daily)
        daily_bytes = os.path.getsize(daily_path)

    minute_rows = 0
    minute_bytes = 0
    if os.path.exists(minute_path):
        df_min = pd.read_csv(minute_path)
        minute_rows = len(df_min)
        minute_bytes = os.path.getsize(minute_path)

    news_count = 0
    news_bytes = 0
    if os.path.exists(news_path):
        with open(news_path, "r", encoding="utf-8") as f:
            news = json.load(f)
            news_count = len(news)
        news_bytes = os.path.getsize(news_path)

    total_records = daily_rows + minute_rows + news_count
    total_bytes = daily_bytes + minute_bytes + news_bytes
    total_mb = round(total_bytes / (1024 * 1024), 3)

    stats = {
        "volume": {
            "total_records": total_records,
            "daily_price_rows": daily_rows,
            "minute_price_rows": minute_rows,
            "news_documents": news_count,
            "total_raw_size_mb": total_mb
        },
        "velocity": {
            "batch_frequency": "End of Day (EOD) OHLCV",
            "simulated_stream_rate": "20 ticks/sec",
            "news_polling_interval": "15 minutes"
        },
        "variety": {
            "structured_data": ["OHLCV CSV tables", "Price matrices"],
            "semi_structured_data": ["JSON API responses", "RSS XML feeds"],
            "unstructured_data": ["Financial news headline text"]
        }
    }

    out_dir = os.path.join("reports")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "dataset_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    return stats


if __name__ == "__main__":
    s = analyze_dataset_characteristics()
    print("Module 1 Dataset Characteristics:")
    print(json.dumps(s, indent=2))
