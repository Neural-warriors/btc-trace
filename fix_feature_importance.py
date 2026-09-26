import re

with open("ml/scoring/alert_generator.py", "r") as f:
    content = f.read()

replacement = """    def _get_top_features(self, features: Dict[str, Any], feature_importance: Dict[str, float], top_k: int = 5) -> List[Dict[str, float]]:
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
                    
        return [{k: v} for k, v in sorted_items[:top_k]]"""

content = re.sub(r"    def _get_top_features.*?return \[\{k: v\} for k, v in sorted_items\[:top_k\]\]", replacement, content, flags=re.DOTALL)

with open("ml/scoring/alert_generator.py", "w") as f:
    f.write(content)
