#!/usr/bin/env python3
"""
Train Time Series Predictor - LSTM/GRU Training Script
Usage: python train_time_series_predictor.py [--hours 168] [--model-type LSTM]
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unified_core.ml.time_series_predictor import (
    TimeSeriesPredictor, PredictionConfig, MetricsData
)
from unified_core.ml.metrics_collector import get_metrics_collector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("train_predictor")


def convert_to_metrics_data(system_metrics_list):
    """Convert SystemMetrics to MetricsData."""
    return [
        MetricsData(
            timestamp=m.timestamp,
            cpu_percent=m.cpu_percent,
            memory_percent=m.memory_percent,
            disk_percent=m.disk_percent,
            gpu_percent=m.gpu_percent,
            gpu_temp=m.gpu_temp
        )
        for m in system_metrics_list
    ]


def main():
    parser = argparse.ArgumentParser(description="Train Time Series Predictor")
    parser.add_argument('--hours', type=int, default=168,
                        help='Hours of historical data to use (default: 168 = 1 week)')
    parser.add_argument('--model-type', choices=['LSTM', 'GRU'], default='LSTM',
                        help='Model type (default: LSTM)')
    parser.add_argument('--hidden-size', type=int, default=64,
                        help='Hidden size (default: 64)')
    parser.add_argument('--num-layers', type=int, default=2,
                        help='Number of layers (default: 2)')
    parser.add_argument('--epochs', type=int, default=50,
                        help='Number of epochs (default: 50)')
    parser.add_argument('--batch-size', type=int, default=32,
                        help='Batch size (default: 32)')
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("🧠 NOOGH Time Series Predictor Training")
    logger.info("=" * 70)

    # 1. Load historical data
    logger.info(f"\n📊 Loading {args.hours}h of historical data...")
    collector = get_metrics_collector()
    system_metrics = collector.get_recent_metrics(hours=args.hours)

    if len(system_metrics) < 1000:
        logger.error(f"❌ Not enough data: {len(system_metrics)} samples")
        logger.error("   Need at least 1000 samples (~3 hours at 10s interval)")
        logger.error("\n💡 Solution: Run metrics_collector for a few hours first:")
        logger.error("   python src/unified_core/ml/metrics_collector.py")
        return 1

    logger.info(f"✅ Loaded {len(system_metrics)} samples")

    # Convert to MetricsData
    metrics_data = convert_to_metrics_data(system_metrics)

    # 2. Create config
    config = PredictionConfig(
        model_type=args.model_type,
        hidden_size=args.hidden_size,
        num_layers=args.num_layers,
        num_epochs=args.epochs,
        batch_size=args.batch_size
    )

    logger.info(f"\n🔧 Model Configuration:")
    logger.info(f"   Type: {config.model_type}")
    logger.info(f"   Hidden Size: {config.hidden_size}")
    logger.info(f"   Layers: {config.num_layers}")
    logger.info(f"   Sequence Length: {config.sequence_length}")
    logger.info(f"   Prediction Horizon: {config.prediction_horizon}")
    logger.info(f"   Features: {', '.join(config.features)}")

    # 3. Create predictor
    predictor = TimeSeriesPredictor(config)

    # 4. Prepare data
    logger.info(f"\n📦 Preparing training data...")
    train_loader, val_loader = predictor.prepare_data(metrics_data, train_split=0.8)

    # 5. Build model
    logger.info(f"\n🏗️  Building {config.model_type} model...")
    predictor.build_model()

    # 6. Train
    logger.info(f"\n🚀 Starting training ({config.num_epochs} epochs)...")
    predictor.train(train_loader, val_loader)

    # 7. Test prediction
    logger.info(f"\n🧪 Testing prediction...")
    recent = metrics_data[-config.sequence_length:]
    predictions = predictor.predict(recent)

    logger.info(f"\n📈 Sample predictions (next {config.prediction_horizon} steps):")
    for feature in config.features:
        values = predictions[feature][:3]  # Show first 3
        logger.info(f"   {feature}: {[round(v, 2) for v in values]}...")

    # 8. Summary
    logger.info("\n" + "=" * 70)
    logger.info("✅ Training Complete!")
    logger.info("=" * 70)
    logger.info(f"\n📊 Final Training Loss: {predictor.train_losses[-1]:.4f}")
    logger.info(f"📊 Final Validation Loss: {predictor.val_losses[-1]:.4f}")
    logger.info(f"\n💾 Model saved to: {config.model_dir}/final_model.pt")
    logger.info("\n📋 Next steps:")
    logger.info("   1. The model is now ready to use")
    logger.info("   2. Integration with PerformanceTrigger is automatic")
    logger.info("   3. Predictions will be used for proactive resource management")

    return 0


if __name__ == "__main__":
    sys.exit(main())
