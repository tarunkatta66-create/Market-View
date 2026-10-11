import os
import pandas as pd
import numpy as np
from typing import Optional
from marketpulse.storage.mongo_client import MongoStore


def run_daily_returns_spark(raw_csv_path: Optional[str] = None, force_pandas: bool = True) -> pd.DataFrame:
    path = raw_csv_path or os.path.join("data", "raw", "prices_daily.csv")
    if not os.path.exists(path):
        from marketpulse.ingest.download_data import fetch_historical_daily
        df_raw = fetch_historical_daily()
    else:
        df_raw = pd.read_csv(path)

    pyspark_df = None

    if not force_pandas:
        try:
            from pyspark.sql import SparkSession
            from pyspark.sql import functions as F
            from pyspark.sql.window import Window

            spark = SparkSession.builder \
                .appName("MarketPulseDailyReturns") \
                .master("local[1]") \
                .config("spark.driver.host", "localhost") \
                .getOrCreate()

            sdf = spark.createDataFrame(df_raw)
            window_spec = Window.partitionBy("Ticker").orderBy("Date")

            sdf = sdf.withColumn("DailyReturn", (F.col("Close") - F.col("Open")) / F.col("Open"))
            sdf = sdf.withColumn("LogReturn", F.log(F.col("Close") / F.col("Open")))
            sdf = sdf.withColumn("MA7", F.avg("Close").over(window_spec.rowsBetween(-6, 0)))
            sdf = sdf.withColumn("Vol7", F.stddev("DailyReturn").over(window_spec.rowsBetween(-6, 0)))

            pyspark_df = sdf.toPandas()
            spark.stop()
        except Exception as e:
            pyspark_df = None

    if pyspark_df is None:
        df = df_raw.copy()
        df = df.sort_values(by=["Ticker", "Date"]).reset_index(drop=True)
        df["DailyReturn"] = (df["Close"] - df["Open"]) / df["Open"]
        df["LogReturn"] = np.log(df["Close"] / df["Open"])

        ma7_list = []
        vol7_list = []
        for ticker, group in df.groupby("Ticker"):
            ma7 = group["Close"].rolling(window=7, min_periods=1).mean()
            vol7 = group["DailyReturn"].rolling(window=7, min_periods=1).std().fillna(0.0)
            ma7_list.extend(ma7)
            vol7_list.extend(vol7)

        df["MA7"] = ma7_list
        df["Vol7"] = vol7_list
        pyspark_df = df

    pyspark_df["DailyReturn"] = pyspark_df["DailyReturn"].round(4)
    pyspark_df["LogReturn"] = pyspark_df["LogReturn"].round(4)
    pyspark_df["MA7"] = pyspark_df["MA7"].round(2)
    pyspark_df["Vol7"] = pyspark_df["Vol7"].round(4)

    proc_dir = os.path.join("data", "processed")
    os.makedirs(proc_dir, exist_ok=True)
    pyspark_df.to_csv(os.path.join(proc_dir, "daily_returns.csv"), index=False)

    store = MongoStore()
    records = pyspark_df.to_dict(orient="records")
    store.clear_collection("daily_returns")
    store.insert_records("daily_returns", records)

    return pyspark_df


if __name__ == "__main__":
    res = run_daily_returns_spark(force_pandas=False)
    print(f"Daily returns computed for {len(res)} rows.")
