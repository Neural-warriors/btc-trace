import pandas as pd
import numpy as np
import logging
from typing import List
from pathlib import Path

from .transaction_features import extract_transaction_features
from .temporal_features import extract_temporal_features
from .network_features import extract_network_features

logger = logging.getLogger(__name__)


def combine_features(df: pd.DataFrame) -> pd.DataFrame:
    """Master feature engineering orchestrator.

    Calls transaction, temporal, and network feature extractors,
    merges results, and returns a single numeric feature DataFrame.
    Wallet and graph features are skipped at the transaction level
    (they aggregate across entities, not rows).
    """
    if df.empty:
        return pd.DataFrame()

    parts = []

    # Transaction features
    try:
        t_feat = extract_transaction_features(df)
        parts.append(t_feat)
        logger.info("Transaction features: %d columns", t_feat.shape[1])
    except Exception as e:
        logger.warning("Transaction feature extraction failed: %s", e)

    # Temporal features
    try:
        temp_feat = extract_temporal_features(df)
        parts.append(temp_feat)
        logger.info("Temporal features: %d columns", temp_feat.shape[1])
    except Exception as e:
        logger.warning("Temporal feature extraction failed: %s", e)

    # Network features
    try:
        n_feat = extract_network_features(df)
        parts.append(n_feat)
        logger.info("Network features: %d columns", n_feat.shape[1])
    except Exception as e:
        logger.warning("Network feature extraction failed: %s", e)

    if not parts:
        return pd.DataFrame(index=df.index)

    features = pd.concat(parts, axis=1)

    # Keep only numeric columns
    features = features.select_dtypes(include=[np.number])

    # Handle missing values
    features = features.fillna(0.0)

    # Preserve is_anomaly label if it exists
    if "is_anomaly" in df.columns:
        features["is_anomaly"] = df["is_anomaly"].values

    logger.info("Combined features: %d rows x %d columns", features.shape[0], features.shape[1])
    return features


def save_features(features_df: pd.DataFrame, path: Path) -> None:
    """Save features to parquet."""
    path.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_parquet(path, index=False)


def load_features(path: Path) -> pd.DataFrame:
    """Load features from parquet."""
    return pd.read_parquet(path)
