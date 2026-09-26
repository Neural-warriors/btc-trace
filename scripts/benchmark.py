import time
import psutil
import os
import gc
from pathlib import Path
import pandas as pd
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ml.features.feature_engineering import combine_features
from ml.models.isolation_forest import IsolationForestModel

def run_benchmarks():
    print("=== BTC-TRACE ML Pipeline Benchmarks ===")
    
    # 1. Feature Engineering Benchmark
    print("\n1. Feature Engineering Benchmark")
    try:
        df = pd.read_parquet('data/splits/test/test.parquet')
        
        # Take 1000 rows
        if len(df) > 1000:
            df = df.head(1000)
            
        print(f"Running on {len(df)} transactions...")
        
        start_time = time.time()
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / (1024 * 1024)
        
        features = combine_features(df)
        
        mem_after = process.memory_info().rss / (1024 * 1024)
        end_time = time.time()
        
        duration = end_time - start_time
        tx_per_sec = len(df) / duration if duration > 0 else 0
        
        print(f"Time taken: {duration:.4f} seconds")
        print(f"Throughput: {tx_per_sec:.2f} tx/sec")
        print(f"Memory used: {mem_after - mem_before:.2f} MB")
        print(f"Features extracted: {features.shape[1]}")
        
    except Exception as e:
        print(f"Feature engineering benchmark failed: {e}")

    # 2. Model Inference Benchmark
    print("\n2. Model Inference Benchmark (Isolation Forest)")
    try:
        model_path = Path('models/isolation_forest.joblib')
        if not model_path.exists():
            print("Model not found. Run 'make train' first.")
            return
            
        model = IsolationForestModel.load(model_path)
        
        n_features = model.model.n_features_in_ if hasattr(model.model, 'n_features_in_') else 25
        X = np.random.rand(10000, n_features)
        
        print(f"Running inference on {len(X)} records...")
        
        start_time = time.time()
        
        scores = model.score_samples(X)
        
        end_time = time.time()
        duration = end_time - start_time
        records_per_sec = len(X) / duration if duration > 0 else 0
        
        print(f"Time taken: {duration:.4f} seconds")
        print(f"Throughput: {records_per_sec:.2f} records/sec")
        print(f"Mean score: {np.mean(scores):.4f}")
        
    except Exception as e:
        print(f"Model inference benchmark failed: {e}")
        
if __name__ == "__main__":
    run_benchmarks()
