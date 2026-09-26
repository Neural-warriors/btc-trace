import re

with open("backend/services/data_service.py", "r") as f:
    content = f.read()

get_metrics_replacement = """    def get_metrics(self) -> Dict[str, Any]:
        with self.lock:
            if not self.data_loaded:
                return {}
            
            try:
                res = self.conn.execute("SELECT COUNT(*), COUNT(DISTINCT input_addresses), COUNT(DISTINCT src_ip), COUNT(DISTINCT asn), CAST(MIN(timestamp) AS VARCHAR), CAST(MAX(timestamp) AS VARCHAR) FROM transactions").fetchone()
                if res:
                    total_transactions, total_wallets, total_ips, total_asns, min_time, max_time = res
                else:
                    total_transactions = total_wallets = total_ips = total_asns = 0
                    min_time = max_time = None
                    
                # timeline
                timeline = []
                try:
                    time_res = self.conn.execute("SELECT CAST(DATE_TRUNC('day', CAST(timestamp AS TIMESTAMP)) AS VARCHAR) as date, COUNT(*) as count FROM transactions GROUP BY 1 ORDER BY 1").fetchall()
                    timeline = [{"date": str(r[0]), "count": r[1]} for r in time_res]
                except Exception as e:
                    print("Timeline err", e)
                
                alerts = self.alerts_data
                high = sum(1 for a in alerts if a.get("priority_score", 0) > 0.7)
                med = sum(1 for a in alerts if 0.4 < a.get("priority_score", 0) <= 0.7)
                low = sum(1 for a in alerts if a.get("priority_score", 0) <= 0.4)
                
                self.metrics = {
                    "total_transactions": total_transactions,
                    "total_wallets": total_wallets,
                    "total_ips": total_ips,
                    "total_asns": total_asns,
                    "total_alerts": len(alerts),
                    "high_risk_count": high,
                    "medium_risk_count": med,
                    "low_risk_count": low,
                    "model_accuracy": 0.0,
                    "graph_nodes": total_transactions + total_wallets + total_ips,
                    "graph_edges": total_transactions * 2,
                    "processing_time_seconds": 0.0,
                    "time_range_start": str(min_time) if min_time else None,
                    "time_range_end": str(max_time) if max_time else None,
                    "timeline_data": timeline
                }
                return self.metrics
            except Exception as e:
                print("Metrics error:", e)
                return {}"""

content = re.sub(r"    def get_metrics\(self\) -> Dict\[str, Any\]:.*?return self\.metrics or \{.*?\}", get_metrics_replacement, content, flags=re.DOTALL)

with open("backend/services/data_service.py", "w") as f:
    f.write(content)
