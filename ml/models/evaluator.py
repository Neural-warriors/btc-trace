import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json
from typing import Dict, Any, Optional

def evaluate_anomaly_model(model: Any, X_test: np.ndarray, y_true: Optional[np.ndarray] = None) -> Dict[str, Any]:
    scores = model.score_samples(X_test) if hasattr(model, 'score_samples') else model.score(X_test)
    
    thresholds = [0.5, 0.75, 0.9, 0.95, 0.99]
    alert_volume = {str(t): int(np.sum(scores > t)) for t in thresholds}
    
    metrics = {
        'score_distribution': {
            'mean': float(np.mean(scores)),
            'std': float(np.std(scores)),
            'min': float(np.min(scores)),
            'max': float(np.max(scores)),
            'p50': float(np.percentile(scores, 50)),
            'p90': float(np.percentile(scores, 90)),
            'p99': float(np.percentile(scores, 99))
        },
        'alert_volume_at_thresholds': alert_volume
    }
    
    if y_true is not None:
        from sklearn.metrics import roc_auc_score, average_precision_score
        metrics['roc_auc'] = float(roc_auc_score(y_true, scores))
        metrics['pr_auc'] = float(average_precision_score(y_true, scores))
        
    return metrics

def evaluate_supervised_model(model: Any, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
    return model.evaluate(X_test, y_test)

def compare_models(results: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for model_name, metrics in results.items():
        row = {'Model': model_name}
        if 'roc_auc' in metrics:
            row['ROC AUC'] = metrics['roc_auc']
        if 'pr_auc' in metrics:
            row['PR AUC'] = metrics['pr_auc']
        if 'score_distribution' in metrics:
            row['Mean Score'] = metrics['score_distribution']['mean']
        rows.append(row)
    return pd.DataFrame(rows)

def generate_evaluation_report(results: Dict[str, Any], output_path: Path):
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def plot_score_distribution(scores: np.ndarray, output_path: Path):
    plt.figure(figsize=(10, 6))
    plt.hist(scores, bins=50, density=True, alpha=0.7, color='blue')
    plt.title('Anomaly Score Distribution')
    plt.xlabel('Anomaly Score')
    plt.ylabel('Density')
    plt.grid(True, alpha=0.3)
    plt.savefig(output_path)
    plt.close()

def plot_roc_curve(y_true: np.ndarray, y_scores: np.ndarray, output_path: Path):
    from sklearn.metrics import roc_curve, auc
    fpr, tpr, _ = roc_curve(y_true, y_scores)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic')
    plt.legend(loc="lower right")
    plt.savefig(output_path)
    plt.close()

def plot_pr_curve(y_true: np.ndarray, y_scores: np.ndarray, output_path: Path):
    from sklearn.metrics import precision_recall_curve, average_precision_score
    precision, recall, _ = precision_recall_curve(y_true, y_scores)
    pr_auc = average_precision_score(y_true, y_scores)
    
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, color='blue', lw=2, label=f'PR curve (area = {pr_auc:.2f})')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve')
    plt.legend(loc="lower left")
    plt.savefig(output_path)
    plt.close()
