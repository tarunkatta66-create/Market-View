import pytest
from marketpulse.streaming.flajolet_martin import FlajoletMartin


def test_flajolet_martin_distinct_count():
    fm = FlajoletMartin(num_hashes=16)
    
    # 20 distinct tickers repeated multiple times
    tickers = [f"TICKER_{i}" for i in range(20)]
    stream = tickers * 10  # 200 elements total

    for t in stream:
        fm.add(t)

    exact_distinct = len(set(tickers))
    estimate = fm.estimate()

    # Distinct cardinality estimation within reasonable error factor
    assert estimate >= 1
    assert abs(estimate - exact_distinct) <= 15
