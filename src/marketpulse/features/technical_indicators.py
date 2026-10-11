import pandas as pd
import numpy as np


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def build_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes technical indicators for stock direction prediction without future data leakage.
    Features: MA5, MA20, RSI14, Volatility20, VolChange, Ret1, Ret5
    Target: Target_Up (1 if next day's Close > today's Close, else 0)
    """
    df = df.copy().sort_values(by=["Ticker", "Date"]).reset_index(drop=True)

    featured_dfs = []
    for ticker, group in df.groupby("Ticker"):
        g = group.copy()
        g["Ret1"] = g["Close"].pct_change().fillna(0.0)
        g["Ret5"] = g["Close"].pct_change(5).fillna(0.0)
        g["MA5"] = (g["Close"].rolling(5).mean() / g["Close"] - 1.0).fillna(0.0)
        g["MA20"] = (g["Close"].rolling(20).mean() / g["Close"] - 1.0).fillna(0.0)
        g["RSI14"] = compute_rsi(g["Close"], 14)
        g["Vol20"] = g["Ret1"].rolling(20).std().fillna(0.0)
        g["VolChange"] = g["Volume"].pct_change().fillna(0.0)

        # Shift target to next day's movement so current day features predict TOMORROW's direction
        g["NextClose"] = g["Close"].shift(-1)
        g["Target_Up"] = (g["NextClose"] > g["Close"]).astype(int)

        featured_dfs.append(g)

    result = pd.concat(featured_dfs, ignore_index=True)
    # Replace inf/-inf with nan and drop rows with NaN in NextClose or features
    result = result.replace([np.inf, -np.inf], np.nan)
    feature_cols = ["Ret1", "Ret5", "MA5", "MA20", "RSI14", "Vol20", "VolChange", "NextClose"]
    clean_df = result.dropna(subset=feature_cols).copy()
    return clean_df
