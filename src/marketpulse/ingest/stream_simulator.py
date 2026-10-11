import os
import time
import queue
import threading
import pandas as pd
from typing import Callable, Optional


class StreamSimulator:
    """
    Replays historical minute price data into an in-memory queue to simulate
    a real-time stock ticker stream.
    """

    def __init__(self, csv_path: str = None, speed_factor: float = 0.05):
        self.csv_path = csv_path or os.path.join("data", "raw", "prices_minute.csv")
        self.speed_factor = speed_factor
        self.output_queue: queue.Queue = queue.Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self, callback: Optional[Callable[[dict], None]] = None):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, args=(callback,), daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def _run(self, callback: Optional[Callable[[dict], None]]):
        if not os.path.exists(self.csv_path):
            from marketpulse.ingest.download_data import fetch_historical_minute
            df = fetch_historical_minute()
        else:
            df = pd.read_csv(self.csv_path)

        if df.empty:
            return

        records = df.to_dict(orient="records")
        idx = 0
        total = len(records)

        while self._running and idx < total:
            row = records[idx]
            tick = {
                "timestamp": str(row.get("Timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))),
                "ticker": str(row.get("Ticker", "UNKNOWN")),
                "price": float(row.get("Close", 0.0)),
                "open": float(row.get("Open", 0.0)),
                "high": float(row.get("High", 0.0)),
                "low": float(row.get("Low", 0.0)),
                "volume": float(row.get("Volume", 0.0)),
                "change_pct": round(((float(row.get("Close", 0.0)) - float(row.get("Open", 0.0))) / float(row.get("Open", 1.0))) * 100, 3)
            }
            self.output_queue.put(tick)
            if callback:
                try:
                    callback(tick)
                except Exception:
                    pass

            idx += 1
            if idx >= total:
                idx = 0  # Loop stream replay

            time.sleep(self.speed_factor)
