import json
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np
from pathlib import Path


@dataclass
class RiskWeights:
    anomaly: float = 0.30
    graph: float = 0.20
    temporal: float = 0.20
    network: float = 0.15
    cluster: float = 0.15
    
    def validate(self) -> None:
        total = self.anomaly + self.graph + self.temporal + self.network + self.cluster
        assert abs(total - 1.0) < 1e-6, f'Weights must sum to 1.0, got {total}'


@dataclass
class RiskScore:
    entity_id: str
    entity_type: str  # 'transaction', 'wallet', 'ip'
    anomaly_score: float  # statistical/model unusualness [0-1]
    graph_score: float  # graph-structural concern [0-1]
    temporal_score: float  # temporal pattern concern [0-1]
    network_score: float  # network-layer concern [0-1]
    cluster_score: float  # cluster/community concern [0-1]
    risk_score: float  # fused investigative concern [0-1]
    confidence_score: float  # data completeness & corroboration [0-1]
    priority_score: float  # alert ordering value [0-1]
    component_details: Dict[str, float] = field(default_factory=dict)


class RiskScorer:
    def __init__(self, weights: Optional[RiskWeights] = None, config_path: Optional[Path] = None):
        self.priority_weights = {
            'risk_weight': 0.6,
            'confidence_weight': 0.3,
            'connectivity_weight': 0.1
        }
        
        if config_path and config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                rw = config.get('risk_weights', {})
                self.weights = RiskWeights(
                    anomaly=rw.get('anomaly', 0.30),
                    graph=rw.get('graph', 0.20),
                    temporal=rw.get('temporal', 0.20),
                    network=rw.get('network', 0.15),
                    cluster=rw.get('cluster', 0.15)
                )
                pw = config.get('priority', {})
                self.priority_weights['risk_weight'] = pw.get('risk_weight', 0.6)
                self.priority_weights['confidence_weight'] = pw.get('confidence_weight', 0.3)
                self.priority_weights['connectivity_weight'] = pw.get('connectivity_weight', 0.1)
        else:
            self.weights = weights if weights is not None else RiskWeights()
            
        self.weights.validate()

    def compute_risk(self, anomaly_score: float, graph_score: float, temporal_score: float, 
                     network_score: float, cluster_score: float) -> float:
        return float(
            anomaly_score * self.weights.anomaly +
            graph_score * self.weights.graph +
            temporal_score * self.weights.temporal +
            network_score * self.weights.network +
            cluster_score * self.weights.cluster
        )

    def compute_confidence(self, data_completeness: float, corroborating_evidence_count: int, 
                           model_agreement_score: float) -> float:
        evidence_score = min(1.0, corroborating_evidence_count / 5.0)
        return float(0.4 * data_completeness + 0.3 * evidence_score + 0.3 * model_agreement_score)

    def compute_priority(self, risk_score: float, confidence_score: float, entity_connectivity: float) -> float:
        return float(
            risk_score * self.priority_weights['risk_weight'] +
            confidence_score * self.priority_weights['confidence_weight'] +
            entity_connectivity * self.priority_weights['connectivity_weight']
        )

    def score_entity(self, entity_id: str, entity_type: str, feature_dict: Dict[str, Any], model_scores: Dict[str, float]) -> RiskScore:
        anomaly_score = model_scores.get('anomaly_score', 0.0)
        graph_score = model_scores.get('graph_score', 0.0)
        temporal_score = model_scores.get('temporal_score', 0.0)
        network_score = model_scores.get('network_score', 0.0)
        cluster_score = model_scores.get('cluster_score', 0.0)
        
        risk_score = self.compute_risk(anomaly_score, graph_score, temporal_score, network_score, cluster_score)
        
        data_completeness = feature_dict.get('data_completeness', 0.5)
        evidence_count = feature_dict.get('corroborating_evidence_count', 0)
        model_agreement = feature_dict.get('model_agreement_score', 0.5)
        
        confidence_score = self.compute_confidence(data_completeness, evidence_count, model_agreement)
        
        connectivity = feature_dict.get('entity_connectivity', 0.1)
        priority_score = self.compute_priority(risk_score, confidence_score, connectivity)
        
        return RiskScore(
            entity_id=entity_id,
            entity_type=entity_type,
            anomaly_score=anomaly_score,
            graph_score=graph_score,
            temporal_score=temporal_score,
            network_score=network_score,
            cluster_score=cluster_score,
            risk_score=risk_score,
            confidence_score=confidence_score,
            priority_score=priority_score,
            component_details=model_scores
        )

    def score_batch(self, entities_df: Any, model_scores_dict: Dict[str, Dict[str, float]]) -> List[RiskScore]:
        # entities_df is typically a pandas DataFrame, but keeping it flexible based on type hint requirements
        scores = []
        for idx, row in entities_df.iterrows():
            entity_id = str(row['entity_id'])
            entity_type = str(row.get('entity_type', 'transaction'))
            feature_dict = row.to_dict()
            model_scores = model_scores_dict.get(entity_id, {})
            scores.append(self.score_entity(entity_id, entity_type, feature_dict, model_scores))
        return scores
