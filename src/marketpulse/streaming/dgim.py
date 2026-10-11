from typing import List, Tuple


class Bucket:
    def __init__(self, timestamp: int, size: int):
        self.timestamp = timestamp
        self.size = size

    def __repr__(self):
        return f"Bucket(ts={self.timestamp}, size={self.size})"


class DGIM:
    """
    DGIM (Datar-Gionis-Indyk-Motwani) algorithm for counting 1-bits in a sliding window.
    Guarantees max error <= 50%.
    """

    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.current_timestamp = 0
        self.buckets: List[Bucket] = []

    def update(self, val: int):
        self.current_timestamp += 1
        
        # Expire old buckets outside window
        cutoff = self.current_timestamp - self.window_size
        self.buckets = [b for b in self.buckets if b.timestamp > cutoff]

        if val != 1:
            return

        # Add new bucket of size 1
        new_bucket = Bucket(self.current_timestamp, 1)
        self.buckets.insert(0, new_bucket)

        # Merge buckets to maintain at most 2 buckets per size
        self._merge()

    def _merge(self):
        size_check = 1
        while True:
            # Find buckets of size size_check
            matching_indices = [i for i, b in enumerate(self.buckets) if b.size == size_check]
            if len(matching_indices) >= 3:
                # Merge the oldest two (last two in list of matching)
                idx1 = matching_indices[-2]
                idx2 = matching_indices[-1]

                # Oldest bucket timestamp is preserved for merged bucket
                old_ts = self.buckets[idx2].timestamp
                merged = Bucket(old_ts, size_check * 2)

                # Remove idx2 first (larger index), then idx1
                del self.buckets[idx2]
                del self.buckets[idx1]

                self.buckets.append(merged)
                # Sort descending by timestamp
                self.buckets.sort(key=lambda b: b.timestamp, reverse=True)

                size_check *= 2
            else:
                break

    def count_ones(self, k: int = None) -> int:
        if k is None:
            k = self.window_size

        cutoff = self.current_timestamp - k
        valid_buckets = [b for b in self.buckets if b.timestamp > cutoff]

        if not valid_buckets:
            return 0

        # Sum all bucket sizes except half of the oldest one
        total = 0
        for i, b in enumerate(valid_buckets):
            if i == len(valid_buckets) - 1:
                total += b.size // 2
            else:
                total += b.size
        return total
