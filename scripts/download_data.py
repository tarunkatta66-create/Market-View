import os
import sys

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from marketpulse.ingest.download_data import (
    fetch_historical_daily,
    fetch_historical_minute,
    fetch_news_rss,
    seed_mongodb
)

if __name__ == "__main__":
    print("Executing download script...")
    daily_df = fetch_historical_daily()
    min_df = fetch_historical_minute()
    news = fetch_news_rss()
    seed_mongodb(daily_df, news)
    print("Download and ingestion finished successfully.")
