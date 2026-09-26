with open("backend/services/data_service.py", "r") as f:
    content = f.read()

get_transaction_code = """
    def get_transaction(self, txid: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            if not self.data_loaded:
                return None
            try:
                res = self.conn.execute("SELECT * FROM transactions WHERE txid = ?", [txid]).fetchone()
                if not res:
                    return None
                
                cols = [desc[0] for desc in self.conn.execute("DESCRIBE transactions").fetchall()]
                tx_dict = dict(zip(cols, res))
                
                # Fetch risk score if it's an alert
                risk_score = 0.0
                for a in self.alerts_data:
                    if a.get("entity_id") == txid:
                        risk_score = a.get("risk_score", 0.0)
                        break
                        
                return {
                    "txid": txid,
                    "timestamp": tx_dict.get("timestamp"),
                    "src_ip": tx_dict.get("src_ip"),
                    "dst_ip": tx_dict.get("dst_ip"),
                    "src_port": tx_dict.get("src_port"),
                    "dst_port": tx_dict.get("dst_port"),
                    "input_addresses": [tx_dict.get("input_addresses")] if tx_dict.get("input_addresses") else [],
                    "output_addresses": [tx_dict.get("output_addresses")] if tx_dict.get("output_addresses") else [],
                    "input_amounts": [tx_dict.get("amount_input")] if tx_dict.get("amount_input") else [],
                    "output_amounts": [tx_dict.get("amount_output")] if tx_dict.get("amount_output") else [],
                    "fee": tx_dict.get("amount_fee"),
                    "script_type": tx_dict.get("script_type"),
                    "geo_country": tx_dict.get("geo_country"),
                    "asn": tx_dict.get("asn"),
                    "risk_score": risk_score
                }
            except Exception as e:
                print("Transaction error:", e)
                return None
"""

content = content.replace("data_service = None", get_transaction_code + "\ndata_service = None")

with open("backend/services/data_service.py", "w") as f:
    f.write(content)
