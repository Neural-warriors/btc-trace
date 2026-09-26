import re

with open("backend/services/data_service.py", "r") as f:
    content = f.read()

replacement = """    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        # Check alerts first
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
        
        # If not found in alerts, look up in transactions table
        tx = self.get_transaction(entity_id)
        if tx:
            return {
                "entity_id": entity_id,
                "entity_type": "transaction",
                "risk_score": tx.get("risk_score", 0),
                "confidence_score": 0,
                "priority": 0,
                "category": None,
                "explanation": "Normal transaction.",
                "reasons": [],
                "features": {},
                "transactions": [],
                "ips": [tx.get("src_ip"), tx.get("dst_ip")] if tx.get("src_ip") or tx.get("dst_ip") else [],
                "wallets": tx.get("input_addresses", []) + tx.get("output_addresses", []),
            }
            
        # Try to infer if it's a wallet or IP from alerts (as a linked entity)
        for alert in self.alerts_data:
            if entity_id in alert.get("linked_wallets", []):
                return {
                    "entity_id": entity_id,
                    "entity_type": "wallet",
                    "risk_score": alert.get("risk_score", 0),
                    "confidence_score": 0,
                    "priority": 0,
                    "category": None,
                    "explanation": f"Wallet linked to anomalous transaction {alert.get('entity_id')}.",
                    "reasons": [],
                    "features": {},
                    "transactions": [alert.get("entity_id")],
                    "ips": [],
                    "wallets": [],
                }
            if entity_id in alert.get("linked_ips", []):
                return {
                    "entity_id": entity_id,
                    "entity_type": "ip",
                    "risk_score": alert.get("risk_score", 0),
                    "confidence_score": 0,
                    "priority": 0,
                    "category": None,
                    "explanation": f"IP Address linked to anomalous transaction {alert.get('entity_id')}.",
                    "reasons": [],
                    "features": {},
                    "transactions": [alert.get("entity_id")],
                    "ips": [],
                    "wallets": [],
                }
        return None"""

content = re.sub(r"    def get_entity\(.*?return None", replacement, content, flags=re.DOTALL)

with open("backend/services/data_service.py", "w") as f:
    f.write(content)
