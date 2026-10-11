import random
import pytest
from marketpulse.streaming.dgim import DGIM


def test_dgim_count_against_brute_force():
    random.seed(42)
    window_size = 100
    dgim = DGIM(window_size=window_size)
    
    stream = [random.choice([0, 1]) for _ in range(300)]

    for bit in stream:
        dgim.update(bit)

    # Brute force count of 1s in the last window_size elements
    last_window = stream[-window_size:]
    exact_count = sum(last_window)

    dgim_count = dgim.count_ones(window_size)

    # DGIM theoretical error bound is <= 50%
    if exact_count > 0:
        error = abs(dgim_count - exact_count) / exact_count
        assert error <= 0.50
    else:
        assert dgim_count == 0


def test_dgim_all_ones():
    dgim = DGIM(window_size=50)
    for _ in range(50):
        dgim.update(1)

    exact = 50
    est = dgim.count_ones(50)
    assert abs(est - exact) / exact <= 0.50
