from typing import Dict, Any

CAVEAT = ('Note: Statistical anomaly detection identifies unusual patterns but does not '
          'constitute evidence of criminal activity. IP address associations reflect network '
          'routing and do not prove wallet ownership or user identity.')

class AlertExplainer:
    def __init__(self) -> None:
        pass

    def explain(self, alert: Any) -> str:
        category = alert.alert_category.replace('_', ' ').title()
        
        # Build specific features explanation
        evidence_points = []
        if alert.top_contributing_features:
            for f in alert.top_contributing_features[:3]:
                for k, v in f.items():
                    name = k.replace("_", " ").title()
                    if isinstance(v, (int, float)):
                        if v > 1000:
                            val_str = f"{v:,.0f}"
                        elif isinstance(v, int) or v.is_integer():
                            val_str = f"{int(v)}"
                        else:
                            val_str = f"{v:.2f}"
                    else:
                        val_str = str(v)
                    evidence_points.append(f"{name} ({val_str})")
                    
        feature_text = ""
        if evidence_points:
            if len(evidence_points) == 1:
                feature_text = f"Specifically, the {evidence_points[0]} is highly unusual."
            elif len(evidence_points) == 2:
                feature_text = f"Specifically, the {evidence_points[0]} and {evidence_points[1]} are highly unusual."
            else:
                feature_text = f"Specifically, the {evidence_points[0]}, {evidence_points[1]}, and {evidence_points[2]} are highly unusual."

        explanation = ''
        if alert.alert_category == 'mixing_service':
            explanation = "This often indicates an attempt to obscure the origin of funds by blending them with other transactions."
        elif alert.alert_category == 'high_fan_out':
            explanation = "This behavior is often seen when large amounts are rapidly split and distributed to many different wallets."
        elif alert.alert_category == 'rapid_movement':
            explanation = "This timing anomaly suggests automated or scripted behavior rather than normal human interaction."
        elif alert.alert_category == 'network_anomaly':
            explanation = "This suggests the transaction originated from or interacted with suspicious IP addresses, unusual geographic locations, or known bad actor networks."
        elif alert.alert_category == 'structural_anomaly':
            explanation = "The overall shape and fee structure of this transaction deviates significantly from standard network traffic."
        else:
            explanation = "The system detected multiple anomalous patterns that significantly deviate from normal behavior."

        risk_level = "High" if alert.risk_score >= 0.55 else ("Medium" if alert.risk_score >= 0.45 else "Low")
        
        return f"This {alert.entity_type} was flagged as a {risk_level}-risk {category}. {feature_text} {explanation} {CAVEAT}"

