import json
import joblib
from pathlib import Path
from typing import Dict, Any, List
import datetime
import numpy as np
import hashlib

from .isolation_forest import IsolationForestModel
from .statistical_baseline import ZScoreAnomalyDetector, IQRAnomalyDetector
from .supervised import SupervisedEnsemble

class ModelTrainer:
    def __init__(self, config: dict):
        self.config = config
        self.models = {}
        
    def train_anomaly_models(self, X_train: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
        print("Training Isolation Forest...")
        iforest = IsolationForestModel()
        iforest.fit(X_train, feature_names)
        
        print("Training ZScore Baseline...")
        zscore = ZScoreAnomalyDetector()
        zscore.fit(X_train)
        
        print("Training IQR Baseline...")
        iqr = IQRAnomalyDetector()
        iqr.fit(X_train)
        
        self.models = {
            'iforest': iforest,
            'zscore': zscore,
            'iqr': iqr
        }
        return self.models
        
    def train_supervised_models(self, X_train: np.ndarray, y_train: np.ndarray, 
                              X_val: np.ndarray, y_val: np.ndarray, 
                              feature_names: List[str]) -> Dict[str, Any]:
        print("Training Supervised Ensemble...")
        ensemble = SupervisedEnsemble()
        ensemble.fit(X_train, y_train, X_val, y_val)
        
        self.models['supervised'] = ensemble
        return self.models
        
    def evaluate_all(self, models: dict, X_test: np.ndarray, y_test: np.ndarray = None) -> dict:
        results = {}
        if y_test is not None and 'supervised' in models:
            results['supervised'] = models['supervised'].evaluate(X_test, y_test)
        
        for name, model in models.items():
            if name != 'supervised':
                # For anomaly models without labels, we can just log distribution stats
                scores = model.score_samples(X_test) if hasattr(model, 'score_samples') else model.score(X_test)
                results[name] = {
                    'mean_score': float(np.mean(scores)),
                    'max_score': float(np.max(scores)),
                    'p99_score': float(np.percentile(scores, 99))
                }
        return results
        
    def save_all(self, models: dict, output_dir: Path):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for name, model in models.items():
            model.save(output_dir / f"{name}.joblib")
            
        metadata = {
            'training_timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'random_seed': self.config.get('random_seed', 42),
            'hyperparameters': self.config
        }
        
        with open(output_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
            
    def load_all(self, model_dir: Path) -> dict:
        model_dir = Path(model_dir)
        models = {}
        
        if (model_dir / "iforest.joblib").exists():
            models['iforest'] = IsolationForestModel.load(model_dir / "iforest.joblib")
        if (model_dir / "zscore.joblib").exists():
            models['zscore'] = ZScoreAnomalyDetector.load(model_dir / "zscore.joblib")
        if (model_dir / "iqr.joblib").exists():
            models['iqr'] = IQRAnomalyDetector.load(model_dir / "iqr.joblib")
        if (model_dir / "supervised.joblib").exists():
            models['supervised'] = SupervisedEnsemble.load(model_dir / "supervised.joblib")
            
        self.models = models
        return models
