import re

with open("backend/services/data_service.py", "r") as f:
    content = f.read()

search_replacement = """    def search(self, query: str, entity_type: str = None, **kwargs) -> Tuple[List[Dict[str, Any]], int]:
        results = []
        q = query.lower()
        
        page = kwargs.get("page", 1)
        page_size = kwargs.get("page_size", 20)
        min_risk = kwargs.get("min_risk", 0.0)
        max_risk = kwargs.get("max_risk", 1.0)
        
        # Search alerts
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
                    
        # If few results, search duckdb
        if len(results) < page_size and self.data_loaded:
            try:
                # search txid
                db_res = self.conn.execute("SELECT txid FROM transactions WHERE txid LIKE ? LIMIT ?", [f"%{q}%", page_size]).fetchall()
                for r in db_res:
                    if not any(x["id"] == r[0] for x in results):
                        results.append({
                            "id": r[0],
                            "type": "transaction",
                            "risk_score": 0.0,
                            "description": "Normal transaction record"
                        })
                
                # search ip
                db_res2 = self.conn.execute("SELECT src_ip, dst_ip FROM transactions WHERE src_ip LIKE ? OR dst_ip LIKE ? LIMIT ?", [f"%{q}%", f"%{q}%", page_size]).fetchall()
                for r in db_res2:
                    for ip in r:
                        if ip and q in ip.lower() and not any(x["id"] == ip for x in results):
                            results.append({
                                "id": ip,
                                "type": "ip",
                                "risk_score": 0.0,
                                "description": "IP Address"
                            })
            except Exception as e:
                pass
        
        start = (page - 1) * page_size
        end = start + page_size
        return results[start:end], len(results)"""

content = re.sub(r"    def search\(.*?return results\[start:end\], len\(results\)", search_replacement, content, flags=re.DOTALL)

with open("backend/services/data_service.py", "w") as f:
    f.write(content)
