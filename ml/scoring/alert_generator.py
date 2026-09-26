import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path

from ml.scoring.risk_scorer import RiskScore
from ml.scoring.explainer import AlertExplainer, CAVEAT

@dataclass
class Alert:
    alert_id: str
    entity_id: str
    entity_type: str
    risk_score: float
    confidence_score: float
    priority_score: float
    alert_category: str
    top_contributing_features: List[Dict[str, float]]
    linked_transactions: List[str]
    linked_wallets: List[str]
    linked_ips: List[str]
    graph_metrics: Dict[str, float]
    temporal_evidence: Dict[str, Any]
    network_evidence: Dict[str, Any]
    model_name: str
    model_version: str
    dataset_version: str
    source_records: List[Dict[str, str]]
    explanation: str
    caveat: str
    created_at: str


class AlertGenerator:
    def __init__(self, model_name: str, model_version: str, dataset_version: str) -> None:
        self.model_name = model_name
        self.model_version = model_version
        self.dataset_version = dataset_version
        self.explainer = AlertExplainer()

    def generate_alert(self, risk_score: RiskScore, features: Dict[str, Any], 
                       graph_data: Dict[str, Any], linked_entities: Dict[str, Any]) -> Alert:
        alert_category = self._classify_alert(risk_score.risk_score, features)
        top_features = self._get_top_features(features, features.get('feature_importance', {}), top_k=5)
        
        alert_id = str(uuid.uuid4())
        
        temp_alert = Alert(
            alert_id=alert_id,
            entity_id=risk_score.entity_id,
            entity_type=risk_score.entity_type,
            risk_score=risk_score.risk_score,
            confidence_score=risk_score.confidence_score,
            priority_score=risk_score.priority_score,
            alert_category=alert_category,
            top_contributing_features=top_features,
            linked_transactions=linked_entities.get('transactions', []),
            linked_wallets=linked_entities.get('wallets', []),
            linked_ips=linked_entities.get('ips', []),
            graph_metrics=graph_data.get('metrics', {}),
            temporal_evidence=features.get('temporal_evidence', {}),
            network_evidence=features.get('network_evidence', {}),
            model_name=self.model_name,
            model_version=self.model_version,
            dataset_version=self.dataset_version,
            source_records=features.get('source_records', []),
            explanation="",
            caveat=CAVEAT,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        temp_alert.explanation = self.explainer.explain(temp_alert)
        return temp_alert

    def generate_alerts_batch(self, risk_scores: List[RiskScore], features_df: Any, 
                              graph_data: Dict[str, Any], entity_links: Dict[str, Dict[str, Any]]) -> List[Alert]:
        alerts = []
        for rs in risk_scores:
            try:
                features = features_df.loc[features_df['entity_id'] == rs.entity_id].iloc[0].to_dict()
            except Exception:
                features = {}
            links = entity_links.get(rs.entity_id, {})
            node_graph = graph_data.get(rs.entity_id, {})
            alerts.append(self.generate_alert(rs, features, node_graph, links))
        return alerts

    def _classify_alert(self, risk_score: float, features: Dict[str, Any]) -> str:
        if features.get('is_mixing', False):
            return 'mixing_service'
        elif features.get('fan_out', 0) > 20:
            return 'high_fan_out'
        elif features.get('rapid_movement', False):
            return 'rapid_movement'
        elif features.get('tor_exit_node', False) or features.get('unusual_asn', False):
            return 'network_anomaly'
        elif features.get('unusual_timing', False):
            return 'unusual_timing'
        else:
            return 'structural_anomaly'

    def _get_top_features(self, features: Dict[str, Any], feature_importance: Dict[str, float], top_k: int = 5) -> List[Dict[str, float]]:
        # Find which features deviate most from typical values, or just use global importance
        # But we must return the ACTUAL value of the feature for this specific entity!
        
        if not feature_importance:
            # If no global importance, just pick numerical features sorted by their absolute value as a proxy for 'unusualness'
            # Note: A real ML system uses SHAP here.
            sorted_items = sorted([(k, v) for k, v in features.items() if isinstance(v, (int, float)) and k not in ['is_anomaly', 'timestamp', 'index']], key=lambda x: abs(x[1]), reverse=True)
        else:
            # Use global importance to select the top K features, but return their ACTUAL values for this entity
            top_keys = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            sorted_items = []
            for k, _ in top_keys:
                if k in features and isinstance(features[k], (int, float)):
                    sorted_items.append((k, features[k]))
                    
        return [{k: v} for k, v in sorted_items[:top_k]]

    def _build_explanation(self, alert_category: str, top_features: List[Dict[str, float]], risk_score: float) -> str:
        # Currently handled by AlertExplainer, keeping as stub for backward compat if needed
        return f"Alert for {alert_category} with risk score {risk_score:.2f}."

    def filter_alerts(self, alerts: List[Alert], min_priority: float = 0.3) -> List[Alert]:
        return [a for a in alerts if a.priority_score >= min_priority]

    def rank_alerts(self, alerts: List[Alert]) -> List[Alert]:
        return sorted(alerts, key=lambda a: a.priority_score, reverse=True)

    def save_alerts(self, alerts: List[Alert], path: str) -> None:
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(path_obj, 'w') as f:
            json.dump([asdict(a) for a in alerts], f, indent=2)

    def load_alerts(self, path: str) -> List[Alert]:
        with open(path, 'r') as f:
            data = json.load(f)
            return [Alert(**a) for a in data]
