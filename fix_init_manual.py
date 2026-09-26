import re

with open("backend/services/data_service.py", "r") as f:
    content = f.read()

init_code = """    def __init__(self, data_dir: Path):
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
        
        self.data_loaded = False
        self.model_loaded = False
        
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

# I will replace the entire __init__ method up to set_current_run
content = re.sub(r"    def __init__\(self, data_dir: Path\):.*?    def set_current_run", init_code + "\n\n    def set_current_run", content, flags=re.DOTALL)

with open("backend/services/data_service.py", "w") as f:
    f.write(content)
