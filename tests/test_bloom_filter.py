import pytest
from marketpulse.streaming.bloom_filter import BloomFilter


def test_bloom_filter_no_false_negatives():
    bf = BloomFilter(expected_elements=100, false_positive_rate=0.01)
    items = [f"headline_{i}" for i in range(50)]

    for item in items:
        bf.add(item)

    # Bloom filter must NEVER produce false negatives
    for item in items:
        assert bf.contains(item) is True


def test_bloom_filter_false_positive_rate():
    bf = BloomFilter(expected_elements=100, false_positive_rate=0.05)
    added = [f"news_{i}" for i in range(50)]
    not_added = [f"unknown_news_{i}" for i in range(200)]

    for item in added:
        bf.add(item)

    # Measure actual false positives on unseen elements
    false_positives = sum(1 for item in not_added if bf.contains(item))
    fp_rate = false_positives / len(not_added)

    # Assert FP rate is within acceptable bound
    assert fp_rate <= 0.20
