import json
import logging
from pathlib import Path
from typing import Union, Tuple, Optional
import pandas as pd

logger = logging.getLogger(__name__)


def temporal_split(
    df: pd.DataFrame,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    output_dir: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split data temporally (earliest -> training, latest -> test).

    If output_dir is provided, saves splits as parquet files and a manifest.
    """
    if not isinstance(df.index, pd.RangeIndex):
        df = df.reset_index(drop=True)

    try:
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp").reset_index(drop=True)
        else:
            raise ValueError("No timestamp column")

        n = len(df)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)

        train_df = df.iloc[:train_end].copy()
        val_df = df.iloc[train_end:val_end].copy()
        test_df = df.iloc[val_end:].copy()
        split_method = "temporal"

    except Exception as e:
        logger.warning("Temporal split failed, falling back to sequential split: %s", e)
        n = len(df)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)

        train_df = df.iloc[:train_end].copy()
        val_df = df.iloc[train_end:val_end].copy()
        test_df = df.iloc[val_end:].copy()
        split_method = "sequential_fallback"

    if output_dir is not None:
        save_splits(train_df, val_df, test_df, output_dir, split_method)

    return train_df, val_df, test_df


def save_splits(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: Union[str, Path],
    split_method: str = "temporal",
) -> None:
    """Save split DataFrames as parquet and a JSON manifest."""
    output_dir = Path(output_dir)

    train_dir = output_dir / "train"
    val_dir = output_dir / "validation"
    test_dir = output_dir / "test"

    for d in [train_dir, val_dir, test_dir]:
        d.mkdir(parents=True, exist_ok=True)

    train_df.to_parquet(train_dir / "train.parquet", index=False)
    val_df.to_parquet(val_dir / "validation.parquet", index=False)
    test_df.to_parquet(test_dir / "test.parquet", index=False)

    def get_date_range(frame: pd.DataFrame) -> str:
        if "timestamp" in frame.columns and not frame.empty:
            return f"{frame['timestamp'].min()} to {frame['timestamp'].max()}"
        return "N/A"

    manifest = {
        "split_method": split_method,
        "train": {
            "count": len(train_df),
            "date_range": get_date_range(train_df),
            "file": "train/train.parquet",
        },
        "validation": {
            "count": len(val_df),
            "date_range": get_date_range(val_df),
            "file": "validation/validation.parquet",
        },
        "test": {
            "count": len(test_df),
            "date_range": get_date_range(test_df),
            "file": "test/test.parquet",
        },
    }

    with open(output_dir / "split_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    logger.info(
        "Splits saved: train=%d, val=%d, test=%d (method=%s)",
        len(train_df), len(val_df), len(test_df), split_method,
    )
