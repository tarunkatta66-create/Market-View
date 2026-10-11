from typing import Dict, Any
from marketpulse.streaming.bloom_filter import BloomFilter
from marketpulse.streaming.dgim import DGIM
from marketpulse.streaming.flajolet_martin import FlajoletMartin
from marketpulse.storage.mongo_client import MongoStore


class StreamConsumer:
    """
    Consumer processing incoming stock stream and financial news,
    maintaining DGIM, Bloom Filter, and Flajolet-Martin stats.
    """

    def __init__(self, window_size: int = 500):
        self.bloom_filter = BloomFilter(expected_elements=2000, false_positive_rate=0.01)
        self.dgim_counters: Dict[str, DGIM] = {}
        self.fm_estimator = FlajoletMartin(num_hashes=8)
        self.window_size = window_size
        self.store = MongoStore()
        self.processed_ticks_count = 0

    def process_tick(self, tick: Dict[str, Any]):
        ticker = tick.get("ticker", "UNKNOWN")
        change_pct = tick.get("change_pct", 0.0)

        # 1. Update Flajolet-Martin distinct ticker count
        self.fm_estimator.add(ticker)

        # 2. Update DGIM up-tick binary stream for ticker
        if ticker not in self.dgim_counters:
            self.dgim_counters[ticker] = DGIM(window_size=self.window_size)
        
        is_uptick = 1 if change_pct > 0.0 else 0
        self.dgim_counters[ticker].update(is_uptick)

        self.processed_ticks_count += 1

    def process_headline(self, headline: str) -> bool:
        """
        Deduplicates headline using Bloom Filter.
        Returns True if headline is NEW, False if DUPLICATE.
        """
        if self.bloom_filter.contains(headline):
            return False
        self.bloom_filter.add(headline)
        return True

    def get_summary(self) -> Dict[str, Any]:
        dgim_stats = {
            t: dg.count_ones() for t, dg in self.dgim_counters.items()
        }
        distinct_tickers_est = self.fm_estimator.estimate()
        
        summary = {
            "processed_ticks_count": self.processed_ticks_count,
            "bloom_filter_items_count": self.bloom_filter.count,
            "distinct_tickers_estimated": distinct_tickers_est,
            "dgim_uptick_counts": dgim_stats
        }
        return summary
