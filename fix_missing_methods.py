import re

with open("backend/services/data_service.py", "r") as f:
    content = f.read()

missing_methods = """
    def get_alerts(self, page: int = 1, page_size: int = 50, entity_type: str = None) -> Tuple[List[Dict[str, Any]], int]:
        alerts = self.alerts_data
        if entity_type:
            alerts = [a for a in alerts if a.get("entity_type") == entity_type]
        alerts = sorted(alerts, key=lambda x: x.get("priority_score", 0), reverse=True)
        start = (page - 1) * page_size
        end = start + page_size
        return alerts[start:end], len(alerts)

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        for alert in self.alerts_data:
            if alert.get("entity_id") == entity_id:
                return {
                    "entity_id": entity_id,
                    "entity_type": alert.get("entity_type", "unknown"),
                    "risk_score": alert.get("risk_score", 0),
                    "confidence_score": alert.get("confidence_score", 0),
                    "priority": alert.get("priority_score", 0),
                    "category": alert.get("alert_category"),
                    "explanation": alert.get("explanation"),
                    "reasons": alert.get("top_contributing_features", []),
                    "features": alert.get("features", {}),
                    "transactions": alert.get("linked_transactions", []),
                    "ips": alert.get("linked_ips", []),
                    "wallets": alert.get("linked_wallets", []),
                }
        return None

    def get_entity_neighborhood(self, entity_id: str, max_hops: int = 1, limit: int = 50) -> Dict[str, Any]:
        nodes = []
        edges = []
        for alert in self.alerts_data:
            eid = alert.get("entity_id")
            if eid == entity_id or entity_id == "sample":
                nodes.append({"id": eid, "type": alert.get("entity_type", "transaction"), "risk_score": alert.get("risk_score", 0), "label": eid[:8]})
                for tx in alert.get("linked_transactions", []):
                    if tx != eid:
                        nodes.append({"id": tx, "type": "transaction", "risk_score": 0, "label": tx[:8]})
                        edges.append({"source": eid, "target": tx, "type": "OBSERVED_WITH"})
                for w in alert.get("linked_wallets", []):
                    nodes.append({"id": w, "type": "wallet", "risk_score": 0, "label": w[:8]})
                    edges.append({"source": eid, "target": w, "type": "INPUT_FROM"})
                for ip in alert.get("linked_ips", []):
                    nodes.append({"id": ip, "type": "ip", "risk_score": 0, "label": ip})
                    edges.append({"source": eid, "target": ip, "type": "OBSERVED_WITH"})
        
        unique_nodes = {n["id"]: n for n in nodes}.values()
        return {"nodes": list(unique_nodes)[:limit], "edges": edges[:limit*2]}

    def get_timeline(self) -> Dict[str, Any]:
        metrics = self.get_metrics()
        return {
            "entries": metrics.get("timeline_data", []),
            "time_range_start": metrics.get("time_range_start"),
            "time_range_end": metrics.get("time_range_end")
        }

    def search(self, query: str, entity_type: str = None) -> Tuple[List[Dict[str, Any]], int]:
        results = []
        q = query.lower()
        for alert in self.alerts_data:
            if q in str(alert).lower():
                results.append({
                    "id": alert.get("entity_id"),
                    "type": alert.get("entity_type", "unknown"),
                    "risk_score": alert.get("risk_score", 0),
                    "description": alert.get("explanation", "Alert match")
                })
        return results, len(results)
"""

content = content.replace("data_service = None", missing_methods + "\ndata_service = None")

with open("backend/services/data_service.py", "w") as f:
    f.write(content)
