import pandas as pd
import numpy as np
from typing import List


def _parse_amounts(series: pd.Series) -> pd.DataFrame:
    """Parse semicolon-separated amounts into per-row statistics."""
    results = []
    for val in series:
        if pd.isna(val) or str(val).strip() == "":
            results.append({"total": 0.0, "count": 0, "max": 0.0, "min": 0.0, "mean": 0.0, "std": 0.0})
            continue
        try:
            amounts = [float(x.strip()) for x in str(val).split(";") if x.strip()]
            arr = np.array(amounts)
            results.append({
                "total": float(arr.sum()),
                "count": len(arr),
                "max": float(arr.max()),
                "min": float(arr.min()),
                "mean": float(arr.mean()),
                "std": float(arr.std()) if len(arr) > 1 else 0.0,
            })
        except (ValueError, TypeError):
            results.append({"total": 0.0, "count": 0, "max": 0.0, "min": 0.0, "mean": 0.0, "std": 0.0})
    return pd.DataFrame(results, index=series.index)


def _count_addresses(series: pd.Series) -> pd.Series:
    """Count semicolon-separated addresses."""
    def _count(val):
        if pd.isna(val) or str(val).strip() == "":
            return 0
        return len([x for x in str(val).split(";") if x.strip()])
    return series.apply(_count)


def extract_transaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract transaction-level features from cleaned data with raw fields."""
    features = pd.DataFrame(index=df.index)

    # Parse input amounts
    if "input_amounts" in df.columns:
        in_stats = _parse_amounts(df["input_amounts"])
        features["amount_total_input"] = in_stats["total"]
        features["num_inputs"] = in_stats["count"]
    else:
        features["amount_total_input"] = 0.0
        features["num_inputs"] = 0

    # Parse output amounts
    if "output_amounts" in df.columns:
        out_stats = _parse_amounts(df["output_amounts"])
        features["amount_total_output"] = out_stats["total"]
        features["num_outputs"] = out_stats["count"]
        features["max_single_output"] = out_stats["max"]
        features["min_single_output"] = out_stats["min"]
        features["mean_output"] = out_stats["mean"]
        features["std_output"] = out_stats["std"]
    else:
        for col in ["amount_total_output", "num_outputs", "max_single_output",
                     "min_single_output", "mean_output", "std_output"]:
            features[col] = 0.0

    # Address counts (fallback if amounts aren't parsed)
    if "input_addresses" in df.columns and features["num_inputs"].sum() == 0:
        features["num_inputs"] = _count_addresses(df["input_addresses"])
    if "output_addresses" in df.columns and features["num_outputs"].sum() == 0:
        features["num_outputs"] = _count_addresses(df["output_addresses"])

    # Fee
    if "fee" in df.columns:
        features["amount_fee"] = pd.to_numeric(df["fee"], errors="coerce").fillna(0.0)
    else:
        features["amount_fee"] = 0.0

    # Ratios
    features["input_output_ratio"] = np.where(
        features["amount_total_output"] > 0,
        features["amount_total_input"] / features["amount_total_output"],
        0.0,
    )
    features["fee_ratio"] = np.where(
        features["amount_total_output"] > 0,
        features["amount_fee"] / features["amount_total_output"],
        0.0,
    )

    # Round amount detection
    def is_round(x: float) -> int:
        if x <= 0:
            return 0
        for r in [1.0, 0.5, 0.1, 10.0, 5.0]:
            if abs(x - round(x / r) * r) < 1e-6:
                return 1
        return 0

    features["is_round_amount"] = features["max_single_output"].apply(is_round)

    # Script type encoding
    if "script_type" in df.columns:
        script_dummies = pd.get_dummies(df["script_type"], prefix="script")
        features = pd.concat([features, script_dummies], axis=1)

    return features
