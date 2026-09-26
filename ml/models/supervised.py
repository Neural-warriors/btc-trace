import numpy as np
import joblib
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import precision_recall_curve, auc, roc_auc_score, confusion_matrix, precision_score, recall_score, f1_score
from typing import Dict, Any

class SupervisedEnsemble:
    def __init__(self):
        self.models = {
            'lr': LogisticRegression(class_weight='balanced', max_iter=1000),
            'rf': RandomForestClassifier(class_weight='balanced', n_estimators=100, random_state=42),
            'xgb': XGBClassifier(scale_pos_weight=10, random_state=42, use_label_encoder=False, eval_metric='logloss')
        }
        self.best_model_name = None
        
    def fit(self, X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray):
        for name, model in self.models.items():
            model.fit(X_train, y_train)
        self.select_best_model(X_val, y_val)
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.models[self.best_model_name].predict(X)
        
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.models[self.best_model_name].predict_proba(X)[:, 1]
        
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        preds = self.predict(X_test)
        probs = self.predict_proba(X_test)
        
        precision, recall, _ = precision_recall_curve(y_test, probs)
        pr_auc = auc(recall, precision)
        roc_auc = roc_auc_score(y_test, probs)
        cm = confusion_matrix(y_test, preds)
        
        tn, fp, fn, tp = cm.ravel()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        
        return {
            'precision': precision_score(y_test, preds, zero_division=0),
            'recall': recall_score(y_test, preds, zero_division=0),
            'f1': f1_score(y_test, preds, zero_division=0),
            'pr_auc': pr_auc,
            'roc_auc': roc_auc,
            'confusion_matrix': cm.tolist(),
            'fpr': fpr
        }
        
    def select_best_model(self, X_val: np.ndarray, y_val: np.ndarray) -> str:
        best_auc = -1
        for name, model in self.models.items():
            probs = model.predict_proba(X_val)[:, 1]
            precision, recall, _ = precision_recall_curve(y_val, probs)
            pr_auc = auc(recall, precision)
            if pr_auc > best_auc:
                best_auc = pr_auc
                self.best_model_name = name
        return self.best_model_name
                
    def save(self, path: Path):
        joblib.dump({
            'models': self.models,
            'best_model_name': self.best_model_name
        }, path)
        
    @classmethod
    def load(cls, path: Path) -> 'SupervisedEnsemble':
        data = joblib.load(path)
        inst = cls()
        inst.models = data['models']
        inst.best_model_name = data['best_model_name']
        return inst
