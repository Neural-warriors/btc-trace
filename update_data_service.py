import re

with open("backend/services/data_service.py", "r") as f:
    content = f.read()

# Add current_dataset_id, current_run_id, current_artifacts_dir
init_pattern = r"self\._load_data\(\)"
init_replacement = """self.current_dataset_id = None
        self.current_run_id = None
        self.current_artifacts_dir = None
        self._load_data()"""
content = content.replace(init_pattern, init_replacement)

# Add set_current_run
add_method = """    def set_current_run(self, dataset_id: str, run_id: str, artifacts_dir: Path):
        self.current_dataset_id = dataset_id
        self.current_run_id = run_id
        self.current_artifacts_dir = artifacts_dir

    def _load_data"""
content = content.replace("    def _load_data", add_method)

# Modify _load_data to accept artifacts_dir
# It uses `project_root / "outputs" / "alerts.json"`
# Change to `artifacts_dir / "outputs" / "alerts.json"`
def_load_data_replacement = """    def _load_data(self, artifacts_dir: Optional[Path] = None):
        try:
            if artifacts_dir is None:
                if self.current_artifacts_dir is not None:
                    artifacts_dir = self.current_artifacts_dir
                else:
                    # Fallback to old global paths for initialization if no artifacts exist
                    artifacts_dir = self.data_dir.parent
                    
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

            # Load data into DuckDB
            parquet_path = artifacts_dir / "clean" / "transactions_clean.parquet"
            if not parquet_path.exists() and artifacts_dir == self.data_dir.parent:
                parquet_path = artifacts_dir / "data" / "clean" / "transactions_clean.parquet"

            if parquet_path.exists():
                with self.lock:
                    self.conn.execute(f"CREATE OR REPLACE VIEW transactions AS SELECT * FROM '{parquet_path}'")
                    self.data_loaded = True
            
            self.model_loaded = len(self.alerts_data) > 0
            
            # Recompute metrics to bust cache
            self.get_metrics()
            
        except Exception as e:
            print(f"Error loading data: {e}")"""

# Replace the entire _load_data method
start = content.find("    def _load_data(")
if start != -1:
    end = content.find("    def get_metrics(", start)
    if end != -1:
        content = content[:start] + def_load_data_replacement + "\n\n" + content[end:]

# Update get_metrics
get_metrics_replacement = """    def get_metrics(self) -> Dict[str, Any]:
        with self.lock:
            if not self.data_loaded:
                return {}
            
            # Use DuckDB to get accurate metrics for the active run
            try:
                res = self.conn.execute("SELECT COUNT(*), COUNT(DISTINCT input_addresses), COUNT(DISTINCT src_ip), COUNT(DISTINCT asn), MIN(timestamp), MAX(timestamp) FROM transactions").fetchone()
                total_transactions, total_wallets, total_ips, total_asns, min_time, max_time = res
                
                # ... rest of get_metrics logic
"""
content = content.replace("""    def get_metrics(self) -> Dict[str, Any]:
        with self.lock:
            if not self.data_loaded:
                return {}
            
            try:
                res = self.conn.execute("SELECT COUNT(*), COUNT(DISTINCT input_addresses), COUNT(DISTINCT src_ip), COUNT(DISTINCT asn), MIN(timestamp), MAX(timestamp) FROM transactions").fetchone()""", """    def get_metrics(self) -> Dict[str, Any]:
        with self.lock:
            if not self.data_loaded:
                return {}
            
            try:
                res = self.conn.execute("SELECT COUNT(*), COUNT(DISTINCT input_addresses), COUNT(DISTINCT src_ip), COUNT(DISTINCT asn), MIN(timestamp), MAX(timestamp) FROM transactions").fetchone()""")

with open("backend/services/data_service.py", "w") as f:
    f.write(content)

