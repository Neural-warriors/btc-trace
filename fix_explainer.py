import re

with open("ml/scoring/explainer.py", "r") as f:
    content = f.read()

replacement = """    def explain(self, alert: Any) -> str:
        category = alert.alert_category
        
        # Build specific features explanation
        feature_text = ""
        if alert.top_contributing_features:
            feats = []
            for f in alert.top_contributing_features[:3]:
                for k, v in f.items():
                    # Format feature names
                    name = k.replace("_", " ").title()
                    # Format values nicely
                    if isinstance(v, (int, float)):
                        if v > 1000:
                            val_str = f"{v:,.0f}"
                        elif v < 0.01:
                            val_str = f"{v:.4f}"
                        else:
                            val_str = f"{v:.2f}"
                    else:
                        val_str = str(v)
                    feats.append(f"{name} ({val_str})")
            
            if feats:
                feature_text = f" Top contributing evidence: {', '.join(feats)}."

        explanation = ''
        if category == 'mixing_service':
            explanation = self._explain_mixing(alert.top_contributing_features)
        elif category == 'high_fan_out':
            explanation = self._explain_fan_out(alert.top_contributing_features)
        elif category == 'rapid_movement':
            explanation = self._explain_timing(alert.top_contributing_features)
        elif category == 'network_anomaly':
            explanation = self._explain_network(alert.top_contributing_features)
        elif category == 'structural_anomaly':
            explanation = self._explain_structural(alert.top_contributing_features)
        else:
            explanation = f"Anomalous patterns detected across multiple dimensions."

        base_explanation = f"{alert.entity_type.capitalize()} {alert.entity_id} was flagged for {category.replace('_', ' ')}. {explanation}{feature_text}"
        return f"{base_explanation} {CAVEAT}"
"""

content = re.sub(r"    def explain\(.*?return f\"\{base_explanation\} \{CAVEAT\}\"", replacement, content, flags=re.DOTALL)

with open("ml/scoring/explainer.py", "w") as f:
    f.write(content)
