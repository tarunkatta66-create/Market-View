import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from marketpulse.models.train import train_and_evaluate_all

if __name__ == "__main__":
    print("Training models...")
    metrics = train_and_evaluate_all()
    print("Metrics generated:")
    print(metrics)
