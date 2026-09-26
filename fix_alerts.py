import re

with open("backend/services/data_service.py", "r") as f:
    content = f.read()

replacement = """    def get_alerts(self, page: int = 1, page_size: int = 50, entity_type: str = None, **kwargs) -> Tuple[List[Dict[str, Any]], int]:
        alerts = self.alerts_data
        if entity_type:
            alerts = [a for a in alerts if a.get("entity_type") == entity_type]
            
        min_risk = kwargs.get("min_risk", 0.0)
        max_risk = kwargs.get("max_risk", 1.0)
        category = kwargs.get("category", None)
        
        alerts = [a for a in alerts if min_risk <= a.get("risk_score", 0) <= max_risk]
        if category:
            alerts = [a for a in alerts if a.get("alert_category") == category]
            
        alerts = sorted(alerts, key=lambda x: x.get("priority_score", 0), reverse=True)
        start = (page - 1) * page_size
        end = start + page_size
        return alerts[start:end], len(alerts)"""

content = re.sub(r"    def get_alerts.*?return alerts\[start:end\], len\(alerts\)", replacement, content, flags=re.DOTALL)

with open("backend/services/data_service.py", "w") as f:
    f.write(content)
