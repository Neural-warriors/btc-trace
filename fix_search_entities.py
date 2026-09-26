import re

with open("backend/services/data_service.py", "r") as f:
    content = f.read()

search_replacement = """    def search(self, query: str, entity_type: str = None, **kwargs) -> Tuple[List[Dict[str, Any]], int]:
        results = []
        q = query.lower()
        
        # Get pagination
        page = kwargs.get("page", 1)
        page_size = kwargs.get("page_size", 20)
        min_risk = kwargs.get("min_risk", 0.0)
        max_risk = kwargs.get("max_risk", 1.0)
        
        for alert in self.alerts_data:
            if q in str(alert).lower() or q in alert.get("entity_id", "").lower():
                risk = alert.get("risk_score", 0.0)
                e_type = alert.get("entity_type", "unknown")
                
                if min_risk <= risk <= max_risk and (not entity_type or e_type == entity_type):
                    results.append({
                        "id": alert.get("entity_id"),
                        "type": e_type,
                        "risk_score": risk,
                        "description": alert.get("explanation", "Alert match")
                    })
        
        start = (page - 1) * page_size
        end = start + page_size
        return results[start:end], len(results)"""

content = re.sub(r"    def search\(.*?return results, len\(results\)", search_replacement, content, flags=re.DOTALL)

neighborhood_replacement = """    def get_entity_neighborhood(self, entity_id: str, depth: int = 1, limit: int = 50) -> Dict[str, Any]:
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
        return {"center_entity": entity_id, "nodes": list(unique_nodes)[:limit], "edges": edges[:limit*2]}"""

content = re.sub(r"    def get_entity_neighborhood\(.*?return \{.*?\}", neighborhood_replacement, content, flags=re.DOTALL)

with open("backend/services/data_service.py", "w") as f:
    f.write(content)
