import re

with open("backend/services/data_service.py", "r") as f:
    content = f.read()

init_replacement = """    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.current_dataset_id = None
        self.current_run_id = None
        self.current_artifacts_dir = None
        self.alerts_data = []
        self.metrics = {}
        self.dq = {}
        self.model_info = {}
        self.validation_report = {}
        
        self.data_loaded = False
        self.model_loaded = False
        self.lock = threading.Lock()
        
        # Connect to DuckDB
        import duckdb
        self.conn = duckdb.connect(database=':memory:')
        
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
            self._load_data(data_dir.parent)"""

content = re.sub(r"    def __init__\(self, data_dir: Path\):.*?self\._load_data\(data_dir\.parent\)", init_replacement, content, flags=re.DOTALL)

set_run_replacement = """    def set_current_run(self, dataset_id: str, run_id: str, artifacts_dir: Path):
        with self.lock:
            self.current_dataset_id = dataset_id
            self.current_run_id = run_id
            self.current_artifacts_dir = artifacts_dir
            
            # Persist active run
            active_run_file = self.data_dir / "artifacts" / "active_run.json"
            active_run_file.parent.mkdir(parents=True, exist_ok=True)
            import json
            with open(active_run_file, "w") as f:
                json.dump({"dataset_id": dataset_id, "run_id": run_id, "artifacts_dir": str(artifacts_dir)}, f)"""

content = re.sub(r"    def set_current_run\(self, dataset_id: str, run_id: str, artifacts_dir: Path\):.*?self\.current_artifacts_dir = artifacts_dir", set_run_replacement, content, flags=re.DOTALL)

with open("backend/services/data_service.py", "w") as f:
    f.write(content)
