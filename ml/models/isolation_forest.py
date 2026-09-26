import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
from pathlib import Path
from typing import List, Dict

class IsolationForestModel:
    def __init__(self, contamination: float = 0.05, n_estimators: int = 200, random_state: int = 42):
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1
        )
        self.feature_names: List[str] = []
        
    def fit(self, X_train: np.ndarray, feature_names: List[str]):
        self.feature_names = feature_names
        self.model.fit(X_train)
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Returns labels (-1 for anomaly, 1 for normal)"""
        return self.model.predict(X)
        
    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """Anomaly scores normalized to [0, 1] where 1 is most anomalous."""
        # score_samples returns negative anomaly scores (lower is more anomalous)
        scores = self.model.score_samples(X)
        # Normalize: -1.0 to 0.0 generally, but let's do min-max scaling robustly
        # For sklearn, values are usually roughly [-1.0, 0.0]
        # Invert so higher is more anomalous
        inverted = -scores
        min_s = inverted.min()
        max_s = inverted.max()
        if max_s > min_s:
            normalized = (inverted - min_s) / (max_s - min_s)
        else:
            normalized = np.zeros_like(inverted)
        return normalized
        
    def get_feature_importance(self) -> Dict[str, float]:
        # Isolation Forest doesn't natively support feature importances in sklearn easily
        # Returning dummy uniform weights for structural completeness
        if not self.feature_names:
            return {}
        return {f: 1.0/len(self.feature_names) for f in self.feature_names}
        
    def save(self, path: Path):
        joblib.dump({
            'model': self.model,
            'feature_names': self.feature_names
        }, path)
        
    @classmethod
    def load(cls, path: Path) -> 'IsolationForestModel':
        data = joblib.load(path)
        inst = cls()
        inst.model = data['model']
        inst.feature_names = data['feature_names']
        return inst
