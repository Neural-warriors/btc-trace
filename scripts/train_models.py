#!/usr/bin/env python3
"""BTC-TRACE Model Training Script.

Trains anomaly detection and (optionally) supervised models on the cleaned dataset.
Saves model artifacts, metrics, and evaluation reports.
"""
import sys
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.features.feature_engineering import combine_features, save_features
from ml.models.isolation_forest import IsolationForestModel
from ml.models.statistical_baseline import ZScoreAnomalyDetector, IQRAnomalyDetector
from ml.models.trainer import ModelTrainer
from ml.models.evaluator import (
    evaluate_anomaly_model,
    compare_models,
    generate_evaluation_report,
    plot_score_distribution,
)
from ml.scoring.risk_scorer import RiskScorer, RiskWeights
from ml.scoring.alert_generator import AlertGenerator
from ml.scoring.explainer import AlertExplainer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def compute_dataset_checksum(path: Path) -> str:
    """Compute SHA256 checksum of a dataset file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-dir", type=str, required=True)
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    artifacts_dir = Path(args.artifacts_dir)
    
    # We will look for splits inside artifacts_dir/splits
    data_dir = artifacts_dir
    models_dir = artifacts_dir / "models"
    reports_dir = artifacts_dir / "reports"
    outputs_dir = artifacts_dir / "outputs"
    
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. Load training data ────────────────────────────────────────
    train_path = data_dir / "splits" / "train" / "train.parquet"
    val_path = data_dir / "splits" / "validation" / "validation.parquet"
    test_path = data_dir / "splits" / "test" / "test.parquet"

    if not train_path.exists():
        logger.error("Training data not found at %s. Run 'make ingest' first.", train_path)
        sys.exit(1)

    logger.info("Loading training data...")
    train_df = pd.read_parquet(train_path)
    val_df = pd.read_parquet(val_path)
    test_df = pd.read_parquet(test_path)

    logger.info("Train: %d rows, Val: %d rows, Test: %d rows", len(train_df), len(val_df), len(test_df))

    # ── 2. Feature engineering ───────────────────────────────────────
    logger.info("Extracting features...")
    train_features = combine_features(train_df)
    val_features = combine_features(val_df)
    test_features = combine_features(test_df)

    # Save features
    features_dir = data_dir / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    save_features(train_features, features_dir / "train_features.parquet")
    save_features(val_features, features_dir / "val_features.parquet")
    save_features(test_features, features_dir / "test_features.parquet")

    # Get numeric feature columns
    feature_cols = [
        c for c in train_features.columns
        if train_features[c].dtype in ["float64", "float32", "int64", "int32"]
        and c not in ["is_anomaly", "original_row_number"]
    ]
    logger.info("Using %d features: %s", len(feature_cols), feature_cols[:10])

    X_train = train_features[feature_cols].fillna(0).values
    X_val = val_features[feature_cols].fillna(0).values
    X_test = test_features[feature_cols].fillna(0).values

    # Check for labels
    has_labels = "is_anomaly" in train_features.columns
    y_train = train_features["is_anomaly"].values.astype(int) if has_labels else None
    y_val = val_features["is_anomaly"].values.astype(int) if has_labels else None
    y_test = test_features["is_anomaly"].values.astype(int) if has_labels else None

    # ── 3. Train Phase 1: Anomaly detection models ───────────────────
    logger.info("=== Phase 1: Training anomaly detection models ===")

    # Isolation Forest
    logger.info("Training Isolation Forest...")
    iso_forest = IsolationForestModel(contamination=0.05, n_estimators=200, random_state=42)
    iso_forest.fit(X_train, feature_cols)
    iso_scores_train = iso_forest.score_samples(X_train)
    iso_scores_val = iso_forest.score_samples(X_val)
    iso_scores_test = iso_forest.score_samples(X_test)
    iso_forest.save(models_dir / "isolation_forest.joblib")
    logger.info("  Isolation Forest trained. Mean anomaly score: %.4f", np.mean(iso_scores_test))

    # Z-Score baseline
    logger.info("Training Z-Score detector...")
    zscore = ZScoreAnomalyDetector(threshold=3.0)
    zscore.fit(X_train)
    zscore_scores_test = zscore.score(X_test)
    zscore.save(models_dir / "zscore_detector.joblib")
    logger.info("  Z-Score trained. Mean anomaly score: %.4f", np.mean(zscore_scores_test))

    # IQR baseline
    logger.info("Training IQR detector...")
    iqr = IQRAnomalyDetector()
    iqr.fit(X_train)
    iqr_scores_test = iqr.score(X_test)
    iqr.save(models_dir / "iqr_detector.joblib")
    logger.info("  IQR trained. Mean anomaly score: %.4f", np.mean(iqr_scores_test))

    # ── 4. Evaluate anomaly models ──────────────────────────────────
    logger.info("Evaluating anomaly models...")
    eval_results: Dict[str, Any] = {}

    eval_results["isolation_forest"] = evaluate_anomaly_model(
        iso_forest, X_test, y_test,
    )
    eval_results["zscore"] = evaluate_anomaly_model(
        zscore, X_test, y_test,
    )
    eval_results["iqr"] = evaluate_anomaly_model(
        iqr, X_test, y_test,
    )

    # ── 5. Train Phase 2: Supervised models (if labels exist) ────────
    if has_labels and y_train is not None:
        logger.info("=== Phase 2: Training supervised models (labels found) ===")
        from ml.models.supervised import SupervisedEnsemble

        ensemble = SupervisedEnsemble()
        ensemble.fit(X_train, y_train, X_val, y_val)
        best_name = ensemble.select_best_model(X_val, y_val)
        logger.info("  Best supervised model: %s", best_name)

        supervised_eval = ensemble.evaluate(X_test, y_test)
        eval_results["supervised_" + best_name] = supervised_eval
        ensemble.save(models_dir / "supervised_ensemble.joblib")
    else:
        logger.info("No labels found in training data. Skipping supervised models (Phase 2).")

    # ── 6. Model comparison ──────────────────────────────────────────
    logger.info("Comparing models...")
    comparison = compare_models(eval_results)
    logger.info("\n%s", comparison.to_string())

    # Save evaluation report
    generate_evaluation_report(eval_results, reports_dir / "model_evaluation.json")
    plot_score_distribution(iso_scores_test, reports_dir / "iso_forest_scores.png")

    # ── 7. Select best model and generate risk scores ────────────────
    logger.info("=== Generating risk scores and alerts ===")

    # Use Isolation Forest as primary anomaly scorer
    scorer = RiskScorer()
    alert_gen = AlertGenerator(
        model_name="IsolationForest",
        model_version="1.0.0",
        dataset_version="1.0.0",
    )

    # Compute risk scores for test data
    all_alerts = []
    for i in range(len(test_df)):
        row = test_df.iloc[i]
        features_row = test_features.iloc[i]

        anomaly_score = float(iso_scores_test[i])
        graph_score = anomaly_score * 0.5  # simplified proxy
        temporal_score = float(features_row.get("is_burst", 0.0)) if "is_burst" in features_row.index else 0.0
        network_score = 1.0 - float(features_row.get("is_standard_port", 1.0))
        cluster_score = anomaly_score * 0.3

        model_scores = {
            "anomaly_score": anomaly_score,
            "graph_score": graph_score,
            "temporal_score": temporal_score,
            "network_score": network_score,
            "cluster_score": cluster_score,
        }
        
        # Calculate dynamic evidence count based on how many scores are suspicious (>0.5)
        evidence_count = sum(1 for s in [anomaly_score, graph_score, temporal_score, network_score, cluster_score] if s > 0.5)
        # Data completeness proxy (could check NaN in features_row)
        valid_features = features_row.notna().sum()
        total_features = len(features_row)
        completeness = valid_features / total_features if total_features > 0 else 0.9
        
        feature_dict = {
            "data_completeness": completeness,
            "corroborating_evidence_count": evidence_count,
            "model_agreement_score": 1.0 - (abs(anomaly_score - graph_score) * 0.5), # higher when models agree
            "entity_connectivity": min(1.0, float(features_row.get("num_outputs", 1)) / 10.0),
        }

        risk_result = scorer.score_entity(
            entity_id=str(row.get("txid", f"tx_{i}")),
            entity_type="transaction",
            feature_dict=feature_dict,
            model_scores=model_scores,
        )

        # Only generate alerts for high-risk entities
        if risk_result.risk_score > 0.3:
            full_features = {col: float(features_row[col]) for col in feature_cols if col in features_row.index}
            feature_importance = iso_forest.get_feature_importance()
            full_features["feature_importance"] = feature_importance

            alert = alert_gen.generate_alert(
                risk_score=risk_result,
                features=full_features,
                graph_data={
                    "degree": int(features_row.get("num_outputs", 0)),
                    "clustering": 0.0,
                    "component_size": 1,
                },
                linked_entities={
                    "transactions": [str(row.get("txid", ""))],
                    "wallets": str(row.get("input_addresses", "")).split(";")[:3] if pd.notna(row.get("input_addresses")) else [],
                    "ips": [str(row.get("src_ip", ""))],
                },
            )
            all_alerts.append(alert)

    # Sort by priority
    all_alerts.sort(key=lambda a: a.priority_score, reverse=True)

    # Save alerts
    alert_gen.save_alerts(all_alerts, outputs_dir / "alerts.json")
    logger.info("Generated %d alerts (top priority: %.4f)", len(all_alerts),
                all_alerts[0].priority_score if all_alerts else 0.0)

    # ── 8. Save model metadata ───────────────────────────────────────
    dataset_checksum = compute_dataset_checksum(train_path) if train_path.exists() else "unknown"

    model_meta = {
        "model_name": "IsolationForest",
        "model_version": "1.0.0",
        "model_type": "anomaly_detection",
        "training_date": datetime.now(timezone.utc).isoformat(),
        "feature_count": len(feature_cols),
        "feature_names": feature_cols,
        "hyperparameters": {
            "contamination": 0.05,
            "n_estimators": 200,
            "random_state": 42,
        },
        "metrics": eval_results.get("isolation_forest", {}),
        "dataset_version": "1.0.0",
        "dataset_checksum": dataset_checksum,
        "random_seed": 42,
        "train_rows": len(train_df),
        "val_rows": len(val_df),
        "test_rows": len(test_df),
        "total_alerts": len(all_alerts),
    }
    with open(models_dir / "model_metadata.json", "w") as f:
        json.dump(model_meta, f, indent=2, default=str)

    # ── 9. Save data quality report ──────────────────────────────────
    quality_report_path = reports_dir / "data_quality.json"
    quality_report = {
        "total_records": len(train_df) + len(val_df) + len(test_df),
        "train_records": len(train_df),
        "validation_records": len(val_df),
        "test_records": len(test_df),
        "feature_count": len(feature_cols),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(quality_report_path, "w") as f:
        json.dump(quality_report, f, indent=2)

    # ── 10. Summary ──────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 60)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 60)
    logger.info("Models saved to: %s", models_dir)
    logger.info("  - isolation_forest.joblib")
    logger.info("  - zscore_detector.joblib")
    logger.info("  - iqr_detector.joblib")
    if has_labels:
        logger.info("  - supervised_ensemble.joblib")
    logger.info("  - model_metadata.json")
    logger.info("")
    logger.info("Reports saved to: %s", reports_dir)
    logger.info("  - model_evaluation.json")
    logger.info("  - iso_forest_scores.png")
    logger.info("  - data_quality.json")
    logger.info("")
    logger.info("Alerts saved to: %s", outputs_dir / "alerts.json")
    logger.info("Total alerts: %d", len(all_alerts))
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
