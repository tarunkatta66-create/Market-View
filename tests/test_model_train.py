import os
import json
import pytest
from marketpulse.models.train import train_and_evaluate_all


def test_model_training_and_metrics_generation():
    metrics = train_and_evaluate_all()
    
    assert "logistic_regression" in metrics
    assert "random_forest" in metrics
    assert "lstm" in metrics

    # Verify realistic accuracy range (0.45 to 0.70)
    for model_name, m in metrics.items():
        assert 0.40 <= m["accuracy"] <= 0.75

    metrics_path = os.path.join("reports", "metrics.json")
    assert os.path.exists(metrics_path)
