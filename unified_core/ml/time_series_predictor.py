"""
Time Series Predictor - LSTM-based System Metrics Forecasting
Version: 1.0.0

Predicts future system metrics (CPU, RAM, GPU, Disk) using LSTM/GRU.
Enables proactive resource management and error prevention.
"""

import logging
import os
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
import json

logger = logging.getLogger("unified_core.ml.time_series_predictor")

# Lazy imports for ML libraries
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available - Time Series Predictor disabled")


@dataclass
class PredictionConfig:
    """Configuration for time series prediction."""
    # Model architecture
    model_type: str = "LSTM"  # LSTM or GRU
    hidden_size: int = 64
    num_layers: int = 2
    dropout: float = 0.2

    # Training
    sequence_length: int = 60  # Look back 60 time steps
    prediction_horizon: int = 12  # Predict 12 steps ahead
    batch_size: int = 32
    learning_rate: float = 0.001
    num_epochs: int = 50

    # Data
    features: List[str] = field(default_factory=lambda: [
        "cpu_percent", "memory_percent", "disk_percent",
        "gpu_percent", "gpu_temp"
    ])
    normalize: bool = True

    # Persistence
    model_dir: str = "data/ml_models"
    checkpoint_interval: int = 10


@dataclass
class MetricsData:
    """Single time point of system metrics."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    gpu_percent: float = 0.0
    gpu_temp: float = 0.0

    def to_array(self, features: List[str]) -> np.ndarray:
        """Convert to numpy array based on selected features."""
        return np.array([getattr(self, f) for f in features], dtype=np.float32)


class TimeSeriesDataset(Dataset):
    """PyTorch Dataset for time series data."""

    def __init__(self, data: np.ndarray, seq_len: int, pred_horizon: int):
        """
        Args:
            data: (num_samples, num_features) array
            seq_len: Length of input sequence
            pred_horizon: Number of steps to predict ahead
        """
        self.data = data
        self.seq_len = seq_len
        self.pred_horizon = pred_horizon

    def __len__(self):
        return len(self.data) - self.seq_len - self.pred_horizon + 1

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.seq_len]
        y = self.data[idx + self.seq_len:idx + self.seq_len + self.pred_horizon]
        return torch.FloatTensor(x), torch.FloatTensor(y)


class LSTMPredictor(nn.Module):
    """LSTM-based time series predictor."""

    def __init__(self, input_size: int, hidden_size: int, num_layers: int,
                 output_size: int, dropout: float = 0.2, model_type: str = "LSTM"):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.model_type = model_type

        # LSTM or GRU
        if model_type == "LSTM":
            self.rnn = nn.LSTM(
                input_size, hidden_size, num_layers,
                batch_first=True, dropout=dropout if num_layers > 1 else 0
            )
        else:  # GRU
            self.rnn = nn.GRU(
                input_size, hidden_size, num_layers,
                batch_first=True, dropout=dropout if num_layers > 1 else 0
            )

        self.fc = nn.Linear(hidden_size, output_size)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        rnn_out, _ = self.rnn(x)
        # Take last time step
        last_out = rnn_out[:, -1, :]
        last_out = self.dropout(last_out)
        out = self.fc(last_out)
        return out


class TimeSeriesPredictor:
    """
    Time series predictor for system metrics.

    Uses LSTM/GRU to predict future CPU, RAM, GPU, Disk usage.
    Enables proactive resource management and error prevention.
    """

    def __init__(self, config: Optional[PredictionConfig] = None):
        self.config = config or PredictionConfig()
        self.model: Optional[nn.Module] = None
        self.optimizer: Optional[optim.Optimizer] = None
        self.scaler_mean: Optional[np.ndarray] = None
        self.scaler_std: Optional[np.ndarray] = None

        # Create model directory
        Path(self.config.model_dir).mkdir(parents=True, exist_ok=True)

        # Training history
        self.train_losses: List[float] = []
        self.val_losses: List[float] = []

        logger.info(
            f"TimeSeriesPredictor initialized | "
            f"model={self.config.model_type}, "
            f"features={len(self.config.features)}"
        )

    def _normalize(self, data: np.ndarray) -> np.ndarray:
        """Normalize data to zero mean and unit variance."""
        if self.scaler_mean is None:
            self.scaler_mean = data.mean(axis=0)
            self.scaler_std = data.std(axis=0) + 1e-8  # Avoid division by zero

        return (data - self.scaler_mean) / self.scaler_std

    def _denormalize(self, data: np.ndarray) -> np.ndarray:
        """Denormalize data back to original scale."""
        if self.scaler_mean is None:
            return data
        return data * self.scaler_std + self.scaler_mean

    def prepare_data(self, metrics_history: List[MetricsData],
                    train_split: float = 0.8) -> Tuple[DataLoader, DataLoader]:
        """
        Prepare data for training.

        Args:
            metrics_history: List of historical metrics
            train_split: Fraction of data for training

        Returns:
            train_loader, val_loader
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch not available")

        # Convert to numpy array
        data = np.array([
            m.to_array(self.config.features) for m in metrics_history
        ], dtype=np.float32)

        logger.info(f"Preparing data: {data.shape[0]} samples, {data.shape[1]} features")

        # Normalize
        if self.config.normalize:
            data = self._normalize(data)

        # Split train/val
        split_idx = int(len(data) * train_split)
        train_data = data[:split_idx]
        val_data = data[split_idx:]

        # Create datasets
        train_dataset = TimeSeriesDataset(
            train_data, self.config.sequence_length, self.config.prediction_horizon
        )
        val_dataset = TimeSeriesDataset(
            val_data, self.config.sequence_length, self.config.prediction_horizon
        )

        # Create dataloaders
        train_loader = DataLoader(
            train_dataset, batch_size=self.config.batch_size, shuffle=True
        )
        val_loader = DataLoader(
            val_dataset, batch_size=self.config.batch_size, shuffle=False
        )

        logger.info(
            f"Data prepared: train={len(train_dataset)}, val={len(val_dataset)}"
        )

        return train_loader, val_loader

    def build_model(self):
        """Build the LSTM/GRU model."""
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch not available")

        input_size = len(self.config.features)
        output_size = len(self.config.features) * self.config.prediction_horizon

        self.model = LSTMPredictor(
            input_size=input_size,
            hidden_size=self.config.hidden_size,
            num_layers=self.config.num_layers,
            output_size=output_size,
            dropout=self.config.dropout,
            model_type=self.config.model_type
        )

        self.optimizer = optim.Adam(
            self.model.parameters(), lr=self.config.learning_rate
        )

        # Move to GPU if available
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        try:
            self.model.to(device)
        except Exception as e:
            logger.warning(f"CUDA memory error ({e}), falling back to CPU for time series model")
            device = torch.device("cpu")
            self.model.to(device)

        logger.info(
            f"Model built: {self.config.model_type} | "
            f"params={sum(p.numel() for p in self.model.parameters())} | "
            f"device={device}"
        )

    def train(self, train_loader: DataLoader, val_loader: DataLoader):
        """Train the model."""
        if not TORCH_AVAILABLE or self.model is None:
            raise RuntimeError("Model not built")

        device = next(self.model.parameters()).device
        criterion = nn.MSELoss()

        logger.info(f"Starting training: {self.config.num_epochs} epochs")

        for epoch in range(self.config.num_epochs):
            # Training
            self.model.train()
            train_loss = 0.0

            for batch_x, batch_y in train_loader:
                batch_x = batch_x.to(device)
                batch_y = batch_y.to(device)

                # Flatten batch_y for loss computation
                batch_y_flat = batch_y.reshape(batch_y.size(0), -1)

                self.optimizer.zero_grad()
                outputs = self.model(batch_x)
                loss = criterion(outputs, batch_y_flat)
                loss.backward()
                self.optimizer.step()

                train_loss += loss.item()

            train_loss /= len(train_loader)
            self.train_losses.append(train_loss)

            # Validation
            self.model.eval()
            val_loss = 0.0

            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    batch_x = batch_x.to(device)
                    batch_y = batch_y.to(device)
                    batch_y_flat = batch_y.reshape(batch_y.size(0), -1)

                    outputs = self.model(batch_x)
                    loss = criterion(outputs, batch_y_flat)
                    val_loss += loss.item()

            val_loss /= len(val_loader)
            self.val_losses.append(val_loss)

            # Log progress
            if (epoch + 1) % 10 == 0:
                logger.info(
                    f"Epoch {epoch+1}/{self.config.num_epochs} | "
                    f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}"
                )

            # Save checkpoint
            if (epoch + 1) % self.config.checkpoint_interval == 0:
                self.save_checkpoint(f"checkpoint_epoch_{epoch+1}.pt")

        logger.info("Training complete!")
        self.save_model("final_model.pt")

    def predict(self, recent_metrics: List[MetricsData]) -> Dict[str, List[float]]:
        """
        Predict future metrics.

        Args:
            recent_metrics: Recent metrics history (at least sequence_length samples)

        Returns:
            Dictionary of predicted metrics for each feature
        """
        if not TORCH_AVAILABLE or self.model is None:
            raise RuntimeError("Model not built")

        if len(recent_metrics) < self.config.sequence_length:
            raise ValueError(
                f"Need at least {self.config.sequence_length} samples, "
                f"got {len(recent_metrics)}"
            )

        # Prepare input
        data = np.array([
            m.to_array(self.config.features)
            for m in recent_metrics[-self.config.sequence_length:]
        ], dtype=np.float32)

        if self.config.normalize:
            data = self._normalize(data)

        # Predict
        device = next(self.model.parameters()).device
        self.model.eval()

        with torch.no_grad():
            x = torch.FloatTensor(data).unsqueeze(0).to(device)  # Add batch dim
            output = self.model(x).cpu().numpy()[0]

        # Reshape output
        output = output.reshape(self.config.prediction_horizon, len(self.config.features))

        # Denormalize
        if self.config.normalize:
            output = self._denormalize(output)

        # Format results
        predictions = {
            feature: output[:, i].tolist()
            for i, feature in enumerate(self.config.features)
        }

        logger.debug(f"Predicted {self.config.prediction_horizon} steps ahead")

        return predictions

    def save_model(self, filename: str):
        """Save model and scaler."""
        if not TORCH_AVAILABLE or self.model is None:
            return

        path = Path(self.config.model_dir) / filename

        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scaler_mean': self.scaler_mean,
            'scaler_std': self.scaler_std,
            'config': self.config.__dict__,
            'train_losses': self.train_losses,
            'val_losses': self.val_losses
        }, path)

        logger.info(f"Model saved: {path}")

    def save_checkpoint(self, filename: str):
        """Save training checkpoint."""
        self.save_model(filename)

    def load_model(self, filename: str):
        """Load model and scaler."""
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch not available")

        path = Path(self.config.model_dir) / filename

        if not path.exists():
            raise FileNotFoundError(f"Model not found: {path}")

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        try:
            checkpoint = torch.load(path, map_location=device, weights_only=False)
        except Exception as e:
            logger.warning(f"CUDA memory error ({e}) during load, falling back to CPU")
            device = torch.device("cpu")
            checkpoint = torch.load(path, map_location=device, weights_only=False)

        # Build model if not already built
        if self.model is None:
            self.build_model()

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.scaler_mean = checkpoint['scaler_mean']
        self.scaler_std = checkpoint['scaler_std']
        self.train_losses = checkpoint.get('train_losses', [])
        self.val_losses = checkpoint.get('val_losses', [])

        logger.info(f"Model loaded: {path}")


# Singleton instance
_predictor_instance: Optional[TimeSeriesPredictor] = None

def get_time_series_predictor() -> TimeSeriesPredictor:
    """Get singleton TimeSeriesPredictor instance."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = TimeSeriesPredictor()
    return _predictor_instance
