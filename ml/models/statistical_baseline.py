import numpy as np
import joblib
from pathlib import Path

class ZScoreAnomalyDetector:
    def __init__(self, threshold: float = 3.0):
        self.threshold = threshold
        self.means = None
        self.stds = None
        
    def fit(self, X_train: np.ndarray):
        self.means = np.mean(X_train, axis=0)
        self.stds = np.std(X_train, axis=0)
        # avoid div by zero
        self.stds[self.stds == 0] = 1e-9
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        scores = self.score(X)
        # return -1 for anomaly, 1 for normal to match IForest
        return np.where(scores > 0.5, -1, 1) # simple mapping
        
    def score(self, X: np.ndarray) -> np.ndarray:
        z_scores = np.abs((X - self.means) / self.stds)
        max_z = np.max(z_scores, axis=1)
        # Normalize score where 3.0 -> ~0.5, larger -> closer to 1
        return np.clip(max_z / (self.threshold * 2), 0, 1)
        
    def save(self, path: Path):
        joblib.dump({'means': self.means, 'stds': self.stds, 'thresh': self.threshold}, path)
        
    @classmethod
    def load(cls, path: Path) -> 'ZScoreAnomalyDetector':
        data = joblib.load(path)
        inst = cls(threshold=data['thresh'])
        inst.means = data['means']
        inst.stds = data['stds']
        return inst

class IQRAnomalyDetector:
    def __init__(self, multiplier: float = 1.5):
        self.multiplier = multiplier
        self.q1 = None
        self.q3 = None
        self.iqr = None
        
    def fit(self, X_train: np.ndarray):
        self.q1 = np.percentile(X_train, 25, axis=0)
        self.q3 = np.percentile(X_train, 75, axis=0)
        self.iqr = self.q3 - self.q1
        self.iqr[self.iqr == 0] = 1e-9
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        scores = self.score(X)
        return np.where(scores > 0.5, -1, 1)
        
    def score(self, X: np.ndarray) -> np.ndarray:
        lower_bound = self.q1 - self.multiplier * self.iqr
        upper_bound = self.q3 + self.multiplier * self.iqr
        
        dev_lower = np.maximum(0, lower_bound - X) / self.iqr
        dev_upper = np.maximum(0, X - upper_bound) / self.iqr
        
        max_dev = np.max(np.maximum(dev_lower, dev_upper), axis=1)
        # normalize
        return np.clip(max_dev / self.multiplier, 0, 1)
        
    def save(self, path: Path):
        joblib.dump({'q1': self.q1, 'q3': self.q3, 'iqr': self.iqr, 'mult': self.multiplier}, path)
        
    @classmethod
    def load(cls, path: Path) -> 'IQRAnomalyDetector':
        data = joblib.load(path)
        inst = cls(multiplier=data['mult'])
        inst.q1 = data['q1']
        inst.q3 = data['q3']
        inst.iqr = data['iqr']
        return inst
