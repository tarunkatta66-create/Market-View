import pandas as pd
import numpy as np
import pytest
from marketpulse.features.technical_indicators import build_technical_features


def test_technical_indicators_no_future_leakage():
    # Synthetic price series where prices double in future
    dates = pd.date_range("2026-01-01", periods=35, freq="B").strftime("%Y-%m-%d")
    df1 = pd.DataFrame({
        "Date": dates,
        "Ticker": "TICK1",
        "Open": np.arange(100, 135),
        "High": np.arange(102, 137),
        "Low": np.arange(98, 133),
        "Close": np.arange(101, 136),
        "Volume": np.full(35, 1000)
    })

    # Future prices altered dramatically from day 28 onwards (strictly in the future)
    df2 = df1.copy()
    df2.loc[28:, "Close"] = df2.loc[28:, "Close"] * 10.0

    feat1 = build_technical_features(df1)
    feat2 = build_technical_features(df2)

    # Features up to day 23 MUST be EXACTLY IDENTICAL regardless of day 28+ price changes
    sub1 = feat1.iloc[:5][["MA5", "MA20", "RSI14", "Vol20"]].values
    sub2 = feat2.iloc[:5][["MA5", "MA20", "RSI14", "Vol20"]].values

    np.testing.assert_almost_equal(sub1, sub2, decimal=5)
