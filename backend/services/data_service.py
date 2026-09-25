import json
import duckdb
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

class DataService:
    def __init__(self, data_dir: Path):
        import threading
        self.lock = threading.Lock()
        self.data_dir = data_dir
        self.current_dataset_id = None
        self.current_run_id = None
        self.current_artifacts_dir = None
        self.alerts_data = []
        self.metrics = {}
        self.dq = {}
        self.model_info = {}
        self.validation_report = {}
        self._parquet_path = None  # Store path for thread-safe per-query connections
        
        self.data_loaded = False
        self.model_loaded = False
        
        # Connect to DuckDB
        import duckdb
        self.conn = duckdb.connect(database=':memory:', read_only=False)
        
        # Try to restore active run
        active_run_file = data_dir / "artifacts" / "active_run.json"
        import json
        if active_run_file.exists():
            try:
                with open(active_run_file, "r") as f:
                    data = json.load(f)
                self.current_dataset_id = data.get("dataset_id")
                self.current_run_id = data.get("run_id")
                self.current_artifacts_dir = Path(data.get("artifacts_dir"))
                self._load_data(self.current_artifacts_dir)
            except:
                self._load_data(data_dir.parent)
        else:
            self._load_data(data_dir.parent)

    def set_current_run(self, dataset_id: str, run_id: str, artifacts_dir: Path):
        self.current_dataset_id = dataset_id
        self.current_run_id = run_id
        self.current_artifacts_dir = artifacts_dir
        
        # Persist active run
        active_run_file = self.data_dir / "artifacts" / "active_run.json"
        active_run_file.parent.mkdir(parents=True, exist_ok=True)
        with open(active_run_file, "w") as f:
            json.dump({"dataset_id": dataset_id, "run_id": run_id, "artifacts_dir": str(artifacts_dir)}, f)
        
        # Reload all data from new run
        self._load_data(artifacts_dir)

    def _load_data(self, artifacts_dir: Optional[Path] = None):
        try:
            if artifacts_dir is None:
                if getattr(self, 'current_artifacts_dir', None) is not None:
                    artifacts_dir = self.current_artifacts_dir
                else:
                    artifacts_dir = self.data_dir.parent
                    
            print(f"LOADING DATA FROM: {artifacts_dir}")
            # Load alerts
            alerts_path = artifacts_dir / "outputs" / "alerts.json"
            if alerts_path.exists():
                with open(alerts_path, "r") as f:
                    self.alerts_data = json.load(f)
            else:
                self.alerts_data = []

            # Load model info
            model_info_path = artifacts_dir / "models" / "model_metadata.json"
            if model_info_path.exists():
                with open(model_info_path, "r") as f:
                    self.model_info = json.load(f)
            else:
                self.model_info = {}

            # Load data quality
            dq_path = artifacts_dir / "reports" / "data_quality.json"
            if dq_path.exists():
                with open(dq_path, "r") as f:
                    self.dq = json.load(f)
            else:
                self.dq = {}

            # Load validation report
            # The clean pipeline saves validation report to reports/
            val_report_path = artifacts_dir / "reports" / "transactions_validation_report.json"
            if val_report_path.exists():
                with open(val_report_path, "r") as f:
                    self.validation_report = json.load(f)
            else:
                self.validation_report = {}

            # Store parquet path for thread-safe per-query connections
            parquet_path = artifacts_dir / "clean" / "transactions_clean.parquet"
            if not parquet_path.exists() and artifacts_dir == self.data_dir.parent:
                parquet_path = artifacts_dir / "data" / "clean" / "transactions_clean.parquet"

            if parquet_path.exists():
                self._parquet_path = str(parquet_path)
                with self.lock:
                    self.conn.execute(f"CREATE OR REPLACE VIEW transactions AS SELECT * FROM '{parquet_path}'")
                self.data_loaded = True
                print(f"Parquet ready: {parquet_path}")
            
            self.model_loaded = len(self.alerts_data) > 0
            print(f"Loaded {len(self.alerts_data)} alerts, data_loaded={self.data_loaded}")
            
            # Recompute metrics to bust cache
            self.get_metrics()
            
        except Exception as e:
            print(f"Error loading data: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        if not self.data_loaded:
            return self.metrics or {}
        try:
            cursor = self.conn.cursor()
            res = cursor.execute(
                "SELECT COUNT(*), COUNT(DISTINCT input_addresses), COUNT(DISTINCT src_ip), "
                "COUNT(DISTINCT asn), CAST(MIN(timestamp) AS VARCHAR), CAST(MAX(timestamp) AS VARCHAR) "
                "FROM transactions"
            ).fetchone()
            if res:
                total_transactions, total_wallets, total_ips, total_asns, min_time, max_time = res
            else:
                total_transactions = total_wallets = total_ips = total_asns = 0
                min_time = max_time = None

            # Daily timeline
            timeline = []
            try:
                time_res = cursor.execute(
                    "SELECT CAST(DATE_TRUNC('day', CAST(timestamp AS TIMESTAMP)) AS VARCHAR) as date, "
                    "COUNT(*) as count FROM transactions GROUP BY 1 ORDER BY 1"
                ).fetchall()
                timeline = [{"date": str(r[0]), "count": r[1]} for r in time_res]
            except Exception as e:
                print("Timeline err", e)
            
            cursor.close()

            alerts = self.alerts_data
            # Thresholds MUST match Alerts page frontend (Alerts.tsx getRiskLevel):
            # HIGH  = risk_score >= 0.55
            # MEDIUM = 0.45 <= risk_score < 0.55
            # LOW   = risk_score < 0.45
            high = sum(1 for a in alerts if a.get("risk_score", 0) >= 0.55)
            med  = sum(1 for a in alerts if 0.45 <= a.get("risk_score", 0) < 0.55)
            low  = sum(1 for a in alerts if a.get("risk_score", 0) < 0.45)

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
            return self.metrics or {}



    def get_data_quality(self) -> Dict[str, Any]:
        return self.dq or {
            "total_records": 0, "valid_records": 0, "quarantined_records": 0,
            "missing_values": {}, "duplicate_count": 0, "invalid_fields": {}
        }

    def get_model_info(self) -> Dict[str, Any]:
        return self.model_info or {
            "model_name": "unknown", "model_version": "unknown", "model_type": "unknown",
            "training_date": "1970-01-01T00:00:00Z", "feature_count": 0, "metrics": {},
            "dataset_version": "unknown", "random_seed": 42
        }


    def get_alerts(self, page: int = 1, page_size: int = 50, entity_type: str = None, **kwargs) -> Tuple[List[Dict[str, Any]], int]:
        min_risk = kwargs.get("min_risk", 0.0)
        max_risk = kwargs.get("max_risk", 1.0)
        category = kwargs.get("category", None)
        
        # Build base transaction alerts
        base_alerts = list(self.alerts_data)
        
        # Build synthetic alerts for ASN, Country, Wallet, and IP
        if self.data_loaded:
            try:
                cursor = self.conn.cursor()
                
                # Build map: ip -> (asn, country) from DuckDB for ASN/Country grouping
                ip_meta = {}
                rows = cursor.execute(
                    "SELECT DISTINCT src_ip, asn, geo_country FROM transactions "
                    "WHERE src_ip IS NOT NULL AND asn IS NOT NULL"
                ).fetchall()
                for r in rows:
                    ip_meta[r[0]] = {"asn": r[1], "country": r[2]}
                cursor.close()
                
                # Aggregate alerts by each type
                asn_map: Dict[str, List] = {}
                country_map: Dict[str, List] = {}
                wallet_map: Dict[str, List] = {}
                ip_map: Dict[str, List] = {}
                
                for alert in self.alerts_data:
                    for ip in alert.get("linked_ips", []):
                        ip_map.setdefault(ip, []).append(alert)
                        meta = ip_meta.get(ip, {})
                        if meta.get("asn"):
                            asn_map.setdefault(meta["asn"], []).append(alert)
                        if meta.get("country"):
                            country_map.setdefault(meta["country"], []).append(alert)
                            
                    for wallet in alert.get("linked_wallets", []):
                        wallet_map.setdefault(wallet, []).append(alert)
                
                # Helper to create synthetic alert
                def add_synthetic(map_data, etype, prefix, desc_fn):
                    if entity_type and entity_type.lower() != etype:
                        return
                    for key, linked in map_data.items():
                        risk = max(a.get("risk_score", 0) for a in linked)
                        base_alerts.append({
                            "alert_id": f"{prefix}-{key}",
                            "entity_id": key,
                            "entity_type": etype,
                            "risk_score": risk,
                            "confidence_score": 0.0,
                            "priority_score": risk,
                            "alert_category": "network_anomaly" if etype in ("asn", "country") else "linked_anomaly",
                            "explanation": desc_fn(key, linked, risk),
                            "top_contributing_features": [],
                            "linked_transactions": list({a.get("entity_id") for a in linked})[:5],
                            "linked_wallets": list({w for a in linked for w in a.get("linked_wallets", [])})[:5],
                            "linked_ips": list({ip for a in linked for ip in a.get("linked_ips", [])})[:5],
                            "created_at": linked[0].get("created_at", ""),
                        })

                # Create synthetic alerts
                add_synthetic(asn_map, "asn", "asn", lambda k, l, r: (
                    f"ASN '{k}' is linked to {len(l)} flagged transaction(s) with a max risk score of {r:.2f}. "
                    f"IPs from this autonomous system appeared in suspicious transactions."
                ))
                add_synthetic(country_map, "country", "country", lambda k, l, r: (
                    f"Country '{k}' is linked to {len(l)} flagged transaction(s) with a max risk score of {r:.2f}. "
                    f"IPs geolocated to this country appeared in suspicious transactions."
                ))
                add_synthetic(wallet_map, "wallet", "wallet", lambda k, l, r: (
                    f"Wallet '{k}' is linked to {len(l)} flagged transaction(s) with a max risk score of {r:.2f}. "
                    f"This wallet participated in suspicious activity."
                ))
                add_synthetic(ip_map, "ip", "ip", lambda k, l, r: (
                    f"IP '{k}' is linked to {len(l)} flagged transaction(s) with a max risk score of {r:.2f}. "
                    f"This IP address initiated suspicious transactions."
                ))

            except Exception as e:
                print(f"Synthetic alert build error: {e}")
        
        alerts = base_alerts
        if entity_type:
            alerts = [a for a in alerts if a.get("entity_type", "").lower() == entity_type.lower()]
        
        alerts = [a for a in alerts if min_risk <= a.get("risk_score", 0) <= max_risk]
        if category:
            alerts = [a for a in alerts if a.get("alert_category") == category]
            
        alerts = sorted(alerts, key=lambda x: x.get("priority_score", 0), reverse=True)
        start = (page - 1) * page_size
        end = start + page_size
        return alerts[start:end], len(alerts)

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
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
                    "reasons": [f"{k}: {v}" for d in alert.get("top_contributing_features", []) for k, v in d.items()],
                    "features": alert.get("top_contributing_features", []),
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
        # Collect ALL alerts that reference this wallet/IP so we can aggregate
        wallet_alerts = [a for a in self.alerts_data if entity_id in a.get("linked_wallets", [])]
        ip_alerts     = [a for a in self.alerts_data if entity_id in a.get("linked_ips", [])]
        
        if wallet_alerts:
            # Use the highest-risk alert as the primary source
            primary = max(wallet_alerts, key=lambda a: a.get("risk_score", 0))
            max_risk = primary.get("risk_score", 0)
            avg_confidence = sum(a.get("confidence_score", 0) for a in wallet_alerts) / len(wallet_alerts)
            avg_priority   = sum(a.get("priority_score", 0) for a in wallet_alerts) / len(wallet_alerts)
            
            # Aggregate all linked transactions and IPs across every alert
            all_txids = list({a.get("entity_id") for a in wallet_alerts if a.get("entity_id")})
            all_ips   = list({ip for a in wallet_alerts for ip in a.get("linked_ips", [])})
            all_wallets = list({w for a in wallet_alerts for w in a.get("linked_wallets", []) if w != entity_id})
            
            features = primary.get("top_contributing_features", [])
            category = primary.get("alert_category", "unknown")
            risk_level = "High" if max_risk >= 0.55 else ("Medium" if max_risk >= 0.45 else "Low")
            
            explanation = (
                f"This wallet was observed in {len(wallet_alerts)} flagged transaction(s). "
                f"The highest-risk associated transaction scored {max_risk:.2f} ({risk_level} risk), "
                f"categorised as '{category.replace('_', ' ').title()}'. "
                f"It is linked to {len(all_txids)} suspicious transaction(s) and {len(all_ips)} associated IP(s)."
            )
            
            return {
                "entity_id": entity_id,
                "entity_type": "wallet",
                "risk_score": max_risk,
                "confidence_score": avg_confidence,
                "priority": avg_priority,
                "category": category,
                "explanation": explanation,
                "reasons": [f"{k}: {v}" for d in features for k, v in d.items()],
                "features": features,
                "transactions": all_txids,
                "ips": all_ips,
                "wallets": all_wallets,
            }
        
        if ip_alerts:
            primary = max(ip_alerts, key=lambda a: a.get("risk_score", 0))
            max_risk = primary.get("risk_score", 0)
            avg_confidence = sum(a.get("confidence_score", 0) for a in ip_alerts) / len(ip_alerts)
            avg_priority   = sum(a.get("priority_score", 0) for a in ip_alerts) / len(ip_alerts)
            
            all_txids   = list({a.get("entity_id") for a in ip_alerts if a.get("entity_id")})
            all_wallets = list({w for a in ip_alerts for w in a.get("linked_wallets", [])})
            all_ips     = list({ip for a in ip_alerts for ip in a.get("linked_ips", []) if ip != entity_id})
            
            features = primary.get("top_contributing_features", [])
            category = primary.get("alert_category", "unknown")
            risk_level = "High" if max_risk >= 0.55 else ("Medium" if max_risk >= 0.45 else "Low")
            
            explanation = (
                f"This IP address was observed in {len(ip_alerts)} flagged transaction(s). "
                f"The highest-risk associated transaction scored {max_risk:.2f} ({risk_level} risk), "
                f"categorised as '{category.replace('_', ' ').title()}'. "
                f"It is linked to {len(all_txids)} suspicious transaction(s) and {len(all_wallets)} associated wallet(s)."
            )
            
            return {
                "entity_id": entity_id,
                "entity_type": "ip",
                "risk_score": max_risk,
                "confidence_score": avg_confidence,
                "priority": avg_priority,
                "category": category,
                "explanation": explanation,
                "reasons": [f"{k}: {v}" for d in features for k, v in d.items()],
                "features": features,
                "transactions": all_txids,
                "ips": all_ips,
                "wallets": all_wallets,
            }
        
        # ASN lookup from DuckDB
        if self.data_loaded:
            try:
                cursor = self.conn.cursor()
                asn_rows = cursor.execute(
                    "SELECT asn, COUNT(*) as cnt, COUNT(DISTINCT src_ip) as unique_ips, "
                    "COUNT(DISTINCT geo_country) as unique_countries "
                    "FROM transactions WHERE asn = ? GROUP BY asn",
                    [entity_id]
                ).fetchone()
                if asn_rows:
                    tx_count = asn_rows[1]
                    unique_ips = asn_rows[2]
                    unique_countries = asn_rows[3]
                    
                    # Fetch actual IPs and txids for the supporting evidence
                    ip_rows = cursor.execute(
                        "SELECT DISTINCT src_ip FROM transactions WHERE asn = ? AND src_ip IS NOT NULL LIMIT 20",
                        [entity_id]
                    ).fetchall()
                    all_ips = [r[0] for r in ip_rows if r[0]]
                    
                    txid_rows = cursor.execute(
                        "SELECT txid FROM transactions WHERE asn = ? LIMIT 20",
                        [entity_id]
                    ).fetchall()
                    all_txids = [r[0] for r in txid_rows if r[0]]
                    
                    # Check if any alert IPs overlap with this ASN's IPs
                    asn_ip_set = set(all_ips)
                    linked_alerts = [
                        a for a in self.alerts_data
                        if any(ip in asn_ip_set for ip in a.get("linked_ips", []))
                    ]
                    max_risk = max((a.get("risk_score", 0) for a in linked_alerts), default=0.0)
                    
                    risk_note = (
                        f"Note: {len(linked_alerts)} flagged transaction(s) involve IPs from this ASN "
                        f"(max risk score: {max_risk:.2f}). "
                        if linked_alerts else
                        "No flagged transactions involve IPs from this ASN. Risk score is 0.0. "
                        "This means the model found no anomalous patterns in traffic from this network."
                    )
                    
                    cursor.close()
                    return {
                        "entity_id": entity_id,
                        "entity_type": "asn",
                        "risk_score": max_risk,
                        "confidence_score": 0.0,
                        "priority": max_risk,
                        "category": "network_info",
                        "explanation": (
                            f"Autonomous System '{entity_id}' was observed in {tx_count} transaction(s) "
                            f"across {unique_ips} unique IP address(es) and {unique_countries} country/countries. "
                            f"No anomalous risk score is directly assigned to ASNs. {risk_note}"
                        ),
                        "reasons": [f"Transaction count: {tx_count}", f"Unique IPs: {unique_ips}", f"Linked flagged alerts: {len(linked_alerts)}"],
                        "features": [],
                        "transactions": all_txids,
                        "ips": all_ips,
                        "wallets": [],
                    }
                cursor.close()
            except Exception as e:
                print(f"ASN entity error: {e}")
        
        # Country lookup from DuckDB
        if self.data_loaded:
            try:
                cursor = self.conn.cursor()
                country_rows = cursor.execute(
                    "SELECT geo_country, COUNT(*) as cnt, COUNT(DISTINCT src_ip) as unique_ips, "
                    "COUNT(DISTINCT asn) as unique_asns "
                    "FROM transactions WHERE UPPER(geo_country) = UPPER(?) GROUP BY geo_country",
                    [entity_id]
                ).fetchone()
                if country_rows:
                    tx_count = country_rows[1]
                    unique_ips = country_rows[2]
                    unique_asns = country_rows[3]
                    
                    # Fetch actual IPs for supporting evidence
                    ip_rows = cursor.execute(
                        "SELECT DISTINCT src_ip FROM transactions WHERE UPPER(geo_country) = UPPER(?) AND src_ip IS NOT NULL LIMIT 20",
                        [entity_id]
                    ).fetchall()
                    all_ips = [r[0] for r in ip_rows if r[0]]
                    
                    asn_rows2 = cursor.execute(
                        "SELECT DISTINCT asn FROM transactions WHERE UPPER(geo_country) = UPPER(?) AND asn IS NOT NULL LIMIT 20",
                        [entity_id]
                    ).fetchall()
                    all_asns = [r[0] for r in asn_rows2 if r[0]]
                    
                    txid_rows = cursor.execute(
                        "SELECT txid FROM transactions WHERE UPPER(geo_country) = UPPER(?) LIMIT 20",
                        [entity_id]
                    ).fetchall()
                    all_txids = [r[0] for r in txid_rows if r[0]]
                    
                    # Check if any alert IPs overlap with this country's IPs
                    country_ip_set = set(all_ips)
                    linked_alerts = [
                        a for a in self.alerts_data
                        if any(ip in country_ip_set for ip in a.get("linked_ips", []))
                    ]
                    max_risk = max((a.get("risk_score", 0) for a in linked_alerts), default=0.0)
                    
                    risk_note = (
                        f"Note: {len(linked_alerts)} flagged transaction(s) involve IPs originating from this country "
                        f"(max risk score: {max_risk:.2f}). "
                        if linked_alerts else
                        "No flagged transactions involve IPs from this country. Risk score is 0.0. "
                        "This means the model found no anomalous patterns in traffic from this country."
                    )
                    
                    cursor.close()
                    return {
                        "entity_id": entity_id,
                        "entity_type": "country",
                        "risk_score": max_risk,
                        "confidence_score": 0.0,
                        "priority": max_risk,
                        "category": "network_info",
                        "explanation": (
                            f"Country code '{entity_id}' was observed in {tx_count} transaction(s) "
                            f"across {unique_ips} unique IP address(es) and {unique_asns} ASN(s). "
                            f"No anomalous risk score is directly assigned to countries. {risk_note}"
                        ),
                        "reasons": [f"Transaction count: {tx_count}", f"Unique IPs: {unique_ips}", f"Unique ASNs: {unique_asns}", f"Linked flagged alerts: {len(linked_alerts)}"],
                        "features": [],
                        "transactions": all_txids,
                        "ips": all_ips,
                        "wallets": all_asns,  # Repurpose wallets field to show ASNs
                    }
                cursor.close()
            except Exception as e:
                print(f"Country entity error: {e}")
        
        return None

    def get_entity_neighborhood(self, entity_id: str, depth: int = 1, limit: int = 5000) -> Dict[str, Any]:
        nodes = []
        edges = []
        
        # User requested to show ALL flagged alerts in the graph
        alerts_to_scan = self.alerts_data
        
        for alert in alerts_to_scan:
            eid = alert.get("entity_id")
            if eid == entity_id or entity_id == "sample":
                nodes.append({"id": eid, "type": alert.get("entity_type", "transaction"), "risk_score": alert.get("risk_score", 0), "label": eid[:8]})
                for tx in alert.get("linked_transactions", []):
                    if tx != eid:
                        nodes.append({"id": tx, "type": "transaction", "risk_score": 0, "label": tx[:8]})
                        edges.append({"source": eid, "target": tx, "type": "OBSERVED_WITH"})
                for w in alert.get("linked_wallets", [])[:3]:  # Limit wallets per node
                    nodes.append({"id": w, "type": "wallet", "risk_score": 0, "label": w[:8]})
                    edges.append({"source": eid, "target": w, "type": "INPUT_FROM"})
                for ip in alert.get("linked_ips", [])[:2]:  # Limit IPs per node
                    nodes.append({"id": ip, "type": "ip", "risk_score": 0, "label": ip})
                    edges.append({"source": eid, "target": ip, "type": "OBSERVED_WITH"})
        
        unique_nodes = list({n["id"]: n for n in nodes}.values())
        return {"center_entity": entity_id, "nodes": unique_nodes, "edges": edges}

    def get_timeline(self) -> Dict[str, Any]:
        metrics = self.get_metrics()
        return {
            "entries": metrics.get("timeline_data", []),
            "time_range_start": metrics.get("time_range_start"),
            "time_range_end": metrics.get("time_range_end")
        }

    def search(self, query: str, entity_type: str = None, **kwargs) -> Tuple[List[Dict[str, Any]], int]:
        results = []
        q = query.lower()
        
        page = kwargs.get("page", 1)
        page_size = kwargs.get("page_size", 20)
        min_risk = kwargs.get("min_risk", 0.0)
        max_risk = kwargs.get("max_risk", 1.0)
        
        # Normalise entity_type filter (UI sends "Wallet", we compare lowercase)
        etype_filter = entity_type.lower() if entity_type else None
        
        seen_ids: set = set()
        
        def add(id_: str, type_: str, risk: float, desc: str) -> None:
            if id_ and id_ not in seen_ids:
                seen_ids.add(id_)
                results.append({"id": id_, "type": type_, "risk_score": risk, "description": desc})
        
        # Search alerts data
        for alert in self.alerts_data:
            risk = alert.get("risk_score", 0.0)
            if not (min_risk <= risk <= max_risk):
                continue
            
            entity_id = alert.get("entity_id", "")
            explanation = alert.get("explanation", "Alert match")
            
            # Transaction match
            if etype_filter in (None, "all", "transaction"):
                if q in entity_id.lower():
                    add(entity_id, "transaction", risk, explanation)
            
            # Wallet match — search linked_wallets
            if etype_filter in (None, "all", "wallet"):
                for w in alert.get("linked_wallets", []):
                    if q in w.lower():
                        add(w, "wallet", risk, f"Linked to flagged tx {entity_id[:16]}... (risk {risk:.2f})")
            
            # IP match — search linked_ips
            if etype_filter in (None, "all", "ip"):
                for ip in alert.get("linked_ips", []):
                    if q in ip.lower():
                        add(ip, "ip", risk, f"Linked to flagged tx {entity_id[:16]}... (risk {risk:.2f})")
        
        # Also search DuckDB for txids not in alerts
        if self.data_loaded and etype_filter in (None, "all", "transaction"):
            try:
                cursor = self.conn.cursor()
                db_res = cursor.execute(
                    "SELECT txid FROM transactions WHERE txid LIKE ? LIMIT ?",
                    [f"%{q}%", page_size]
                ).fetchall()
                for r in db_res:
                    add(r[0], "transaction", 0.0, "Normal transaction — no anomalous patterns detected by the model.")
                cursor.close()
            except Exception:
                pass
        
        # Also search DuckDB for IPs (both flagged ones already added above + unflagged ones)
        if self.data_loaded and etype_filter in (None, "all", "ip"):
            try:
                cursor = self.conn.cursor()
                db_res = cursor.execute(
                    "SELECT DISTINCT src_ip FROM transactions WHERE src_ip LIKE ? LIMIT ?",
                    [f"%{q}%", page_size]
                ).fetchall()
                for r in db_res:
                    if r[0]:
                        add(r[0], "ip", 0.0,
                            "IP observed in normal transactions — risk score is 0.0 because the model "
                            "found no anomalous activity associated with this IP address.")
                cursor.close()
            except Exception:
                pass
        
        # Search DuckDB for ASN
        if self.data_loaded and etype_filter in (None, "all", "asn"):
            try:
                cursor = self.conn.cursor()
                db_res = cursor.execute(
                    "SELECT asn, COUNT(*) as cnt FROM transactions "
                    "WHERE UPPER(asn) LIKE UPPER(?) GROUP BY asn ORDER BY cnt DESC LIMIT ?",
                    [f"%{q}%", page_size]
                ).fetchall()
                for r in db_res:
                    asn_val = r[0]
                    tx_count = r[1]
                    if asn_val:
                        add(asn_val, "asn", 0.0,
                            f"Autonomous System Number — observed in {tx_count} transaction(s). "
                            f"No anomalous score assigned to ASNs directly.")
                cursor.close()
            except Exception as e:
                print(f"ASN search error: {e}")
        
        # Search DuckDB for Country
        if self.data_loaded and etype_filter in (None, "all", "country"):
            try:
                cursor = self.conn.cursor()
                db_res = cursor.execute(
                    "SELECT geo_country, COUNT(*) as cnt FROM transactions "
                    "WHERE UPPER(geo_country) LIKE UPPER(?) GROUP BY geo_country ORDER BY cnt DESC LIMIT ?",
                    [f"%{q}%", page_size]
                ).fetchall()
                for r in db_res:
                    country_val = r[0]
                    tx_count = r[1]
                    if country_val:
                        add(country_val, "country", 0.0,
                            f"Country code — seen in {tx_count} transaction(s). "
                            f"No anomalous score is assigned to countries directly.")
                cursor.close()
            except Exception as e:
                print(f"Country search error: {e}")
        
        start = (page - 1) * page_size
        end = start + page_size
        return results[start:end], len(results)


    def get_transaction(self, txid: str) -> Optional[Dict[str, Any]]:
        if not self.data_loaded:
            return None
        try:
            cursor = self.conn.cursor()
            res = cursor.execute("SELECT * FROM transactions WHERE txid = ?", [txid]).fetchone()
            if not res:
                cursor.close()
                return None
            
            cols = [desc[0] for desc in cursor.execute("DESCRIBE transactions").fetchall()]
            tx_dict = dict(zip(cols, res))
            cursor.close()
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
                "input_addresses": tx_dict.get("input_addresses", "").split(";") if tx_dict.get("input_addresses") else [],
                "output_addresses": tx_dict.get("output_addresses", "").split(";") if tx_dict.get("output_addresses") else [],
                "input_amounts": [float(x) for x in str(tx_dict.get("input_amounts", "")).split(";") if x.strip()] if tx_dict.get("input_amounts") else [],
                "output_amounts": [float(x) for x in str(tx_dict.get("output_amounts", "")).split(";") if x.strip()] if tx_dict.get("output_amounts") else [],
                "fee": float(tx_dict.get("fee")) if tx_dict.get("fee") is not None else None,
                "script_type": tx_dict.get("script_type"),
                "geo_country": tx_dict.get("geo_country"),
                "asn": tx_dict.get("asn"),
                "risk_score": risk_score
            }
        except Exception as e:
            print("Transaction error:", e)
            return None

data_service = None
