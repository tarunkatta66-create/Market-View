import math
import hashlib
from typing import List


class BloomFilter:
    """
    Bloom Filter implemented from scratch using bit arrays and salted hash functions.
    Used for headline deduplication.
    """

    def __init__(self, expected_elements: int = 1000, false_positive_rate: float = 0.01):
        self.n = expected_elements
        self.p = false_positive_rate
        # Calculate optimal size m and number of hash functions k
        self.m = int(- (self.n * math.log(self.p)) / (math.log(2) ** 2))
        self.m = max(self.m, 64)
        self.k = int((self.m / self.n) * math.log(2))
        self.k = max(self.k, 1)

        self.bit_array = [False] * self.m
        # Track number of inserted items for diagnostics
        self._inserted = 0

    def _hashes(self, item: str) -> List[int]:
        indexes = []
        item_bytes = str(item).encode('utf-8')
        for seed in range(self.k):
            # Salted SHA256 hash
            digest = hashlib.sha256(item_bytes + bytes([seed])).hexdigest()
            hash_val = int(digest, 16)
            indexes.append(hash_val % self.m)
        return indexes

    def add(self, item: str):
        for idx in self._hashes(item):
            self.bit_array[idx] = True
        self._inserted += 1

    @property
    def count(self) -> int:
        """Return number of items added to the filter."""
        return self._inserted

    def contains(self, item: str) -> bool:
        """Check if item may be in filter (no false negatives)."""
        for idx in self._hashes(item):
            if not self.bit_array[idx]:
                return False
        return True

    def __contains__(self, item: str) -> bool:
        return self.contains(item)
