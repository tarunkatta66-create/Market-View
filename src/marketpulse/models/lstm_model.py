import numpy as np

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


if HAS_TORCH:
    class PyTorchLSTM(nn.Module):
        def __init__(self, input_dim: int = 6, hidden_dim: int = 16, num_layers: int = 1):
            super().__init__()
            self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers=num_layers, batch_first=True)
            self.fc = nn.Linear(hidden_dim, 1)
            self.sigmoid = nn.Sigmoid()

        def forward(self, x):
            # x shape: (batch_size, seq_len, input_dim)
            out, _ = self.lstm(x)
            out = out[:, -1, :]  # Take last time step
            out = self.fc(out)
            return self.sigmoid(out)


class LSTMClassifier:
    """
    LSTM model wrapper with walk-forward support and PyTorch/MLP fallback.
    """

    def __init__(self, input_dim: int = 6, hidden_dim: int = 16):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.model = None

    def fit(self, X: np.ndarray, y: np.ndarray, epochs: int = 20):
        if len(X) == 0:
            return

        if HAS_TORCH:
            self.model = PyTorchLSTM(input_dim=self.input_dim, hidden_dim=self.hidden_dim)
            criterion = nn.BCELoss()
            optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)

            # Reshape 2D X to 3D for LSTM: (batch_size, seq_len=1, input_dim)
            X_tensor = torch.tensor(X, dtype=torch.float32).unsqueeze(1)
            y_tensor = torch.tensor(y, dtype=torch.float32).unsqueeze(1)

            self.model.train()
            for _ in range(epochs):
                optimizer.zero_grad()
                preds = self.model(X_tensor)
                loss = criterion(preds, y_tensor)
                loss.backward()
                optimizer.step()
        else:
            from sklearn.neural_network import MLPClassifier
            self.model = MLPClassifier(hidden_layer_sizes=(16,), max_iter=epochs, random_state=42)
            self.model.fit(X, y)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if len(X) == 0 or self.model is None:
            return np.zeros((len(X), 2))

        if HAS_TORCH:
            self.model.eval()
            with torch.no_grad():
                X_tensor = torch.tensor(X, dtype=torch.float32).unsqueeze(1)
                probs_1 = self.model(X_tensor).numpy().flatten()
                probs_0 = 1.0 - probs_1
                return np.column_stack([probs_0, probs_1])
        else:
            return self.model.predict_proba(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        probs = self.predict_proba(X)
        return (probs[:, 1] >= 0.5).astype(int)
