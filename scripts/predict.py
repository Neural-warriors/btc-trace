#!/usr/bin/env python3
"""BTC-TRACE Inference Script.

Allows the user to feed new CSV/JSON testing data into the trained model
to see how it scores and if it flags any anomalies.
"""
import sys
import argparse
import pandas as pd
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.pipeline.ingest import ingest
from ml.pipeline.validate import validate_record
from ml.pipeline.normalize import normalize_record
from ml.features.feature_engineering import combine_features
from ml.models.isolation_forest import IsolationForestModel
from ml.scoring.risk_scorer import RiskScorer
from ml.scoring.alert_generator import AlertGenerator

def predict_on_new_data(input_file: str, output_file: str = "predictions.json"):
    print(f"1. Loading new data from {input_file}...")
    try:
        raw_df = ingest(input_file)
    except Exception as e:
        print(f"Failed to load file: {e}")
        return

    print(f"   Loaded {len(raw_df)} rows.")

    print("2. Validating and Cleaning data...")
    valid_df, quarantine_df, report = validate_record(raw_df)
    print(f"   Valid: {len(valid_df)}, Quarantined (Invalid): {len(quarantine_df)}")

    if valid_df.empty:
        print("No valid data to score.")
        return

    clean_df = normalize_record(valid_df)

    print("3. Extracting Features...")
    features_df = combine_features(clean_df)
    
    # Keep only columns that were used during training
    model_path = PROJECT_ROOT / "models" / "isolation_forest.joblib"
    if not model_path.exists():
        print("Model not found! Run 'make train' first to train the models.")
        return
        
    print("4. Loading Trained Model (Isolation Forest)...")
    model = IsolationForestModel.load(model_path)
    
    # Match feature columns
    feature_cols = model.feature_names if hasattr(model, 'feature_names') else []
    if not feature_cols:
        # Fallback if metadata wasn't saved perfectly
        feature_cols = [c for c in features_df.columns if features_df[c].dtype in ['float64', 'float32', 'int64', 'int32']]
        
    # Ensure all required columns exist in the new data
    for col in feature_cols:
        if col not in features_df.columns:
            features_df[col] = 0.0
            
    X_new = features_df[feature_cols].fillna(0).values

    print("5. Running Model Inference...")
    anomaly_scores = model.score_samples(X_new)

    scorer = RiskScorer()
    alert_gen = AlertGenerator(
        model_name="IsolationForest",
        model_version="1.0.0",
        dataset_version="New_Data"
    )

    print("6. Generating Risk Scores & Alerts...")
    alerts = []
    results = []
    
    for i in range(len(clean_df)):
        row = clean_df.iloc[i]
        f_row = features_df.iloc[i]
        a_score = float(anomaly_scores[i])
        
        # Approximate component scores based on features
        graph_score = a_score * 0.5 
        temporal_score = float(f_row.get("is_burst", 0.0))
        network_score = 1.0 - float(f_row.get("is_standard_port", 1.0))
        cluster_score = a_score * 0.3
        
        model_scores = {
            "anomaly_score": a_score,
            "graph_score": graph_score,
            "temporal_score": temporal_score,
            "network_score": network_score,
            "cluster_score": cluster_score,
        }
        
        feature_dict = {
            "data_completeness": 0.9,
            "corroborating_evidence_count": 0,
            "model_agreement_score": 0.8,
            "entity_connectivity": min(1.0, float(f_row.get("num_outputs", 1)) / 10.0),
        }

        txid = str(row.get("txid", f"new_tx_{i}"))
        risk_result = scorer.score_entity(
            entity_id=txid,
            entity_type="transaction",
            feature_dict=feature_dict,
            model_scores=model_scores,
        )

        results.append({
            "txid": txid,
            "risk_score": risk_result.risk_score,
            "anomaly_score": a_score,
            "is_flagged": risk_result.risk_score > 0.3
        })

        if risk_result.risk_score > 0.3:
            full_features = {col: float(f_row[col]) for col in feature_cols if col in f_row.index}
            full_features["feature_importance"] = model.get_feature_importance()
            
            alert = alert_gen.generate_alert(
                risk_score=risk_result,
                features=full_features,
                graph_data={"degree": int(f_row.get("num_outputs", 0)), "clustering": 0.0, "component_size": 1},
                linked_entities={
                    "transactions": [txid],
                    "wallets": str(row.get("input_addresses", "")).split(";")[:3] if pd.notna(row.get("input_addresses")) else [],
                    "ips": [str(row.get("src_ip", ""))]
                }
            )
            alerts.append(alert)

    # Sort results by highest risk first
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    alerts.sort(key=lambda a: a.priority_score, reverse=True)

    print(f"\n--- SCORING RESULTS ---")
    print(f"Total evaluated: {len(results)}")
    print(f"High Risk (Anomalies Found): {len(alerts)}")
    
    if alerts:
        print("\nTop 3 Highest Risk Transactions:")
        for a in alerts[:3]:
            print(f" - TXID: {a.entity_id}")
            print(f"   Risk Score: {a.risk_score:.4f} (Category: {a.alert_category})")
            print(f"   Explanation: {a.explanation}")
            print()

    # Save complete results
    output_path = PROJECT_ROOT / output_file
    with open(output_path, "w") as f:
        json.dump({"results": results, "alerts": [a.__dict__ for a in alerts]}, f, indent=2)
        
    print(f"Detailed output saved to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run BTC-TRACE inference on new testing data.")
    parser.add_argument("input_file", help="Path to the new CSV/JSON file containing transactions.")
    parser.add_argument("--output", default="predictions.json", help="Path to save the output predictions.")
    
    args = parser.parse_args()
    predict_on_new_data(args.input_file, args.output)
