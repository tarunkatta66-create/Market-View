import math
import hashlib
from typing import List


class FlajoletMartin:
    """
    Flajolet-Martin algorithm for estimating distinct elements count in a data stream.
    """

    def __init__(self, num_hashes: int = 8):
        self.num_hashes = num_hashes
        self.max_zeros = [0] * num_hashes
        self.phi = 0.77351  # Correction factor constant

    def _hash(self, item: str, seed: int) -> int:
        item_bytes = str(item).encode('utf-8')
        digest = hashlib.md5(item_bytes + bytes([seed])).hexdigest()
        return int(digest[:8], 16)  # 32-bit int

    def _trailing_zeros(self, val: int) -> int:
        if val == 0:
            return 32
        count = 0
        while (val & 1) == 0:
            count += 1
            val >>= 1
        return count

    def add(self, item: str):
        for seed in range(self.num_hashes):
            h_val = self._hash(item, seed)
            r = self._trailing_zeros(h_val)
            if r > self.max_zeros[seed]:
                self.max_zeros[seed] = r

    def estimate(self) -> int:
        estimates = [(2 ** r) / self.phi for r in self.max_zeros]
        estimates.sort()

        # Median estimate across hash groups
        mid = len(estimates) // 2
        if len(estimates) % 2 == 0:
            median_est = (estimates[mid - 1] + estimates[mid]) / 2.0
        else:
            median_est = estimates[mid]

        return int(round(median_est))
