import re

with open("backend/services/data_service.py", "r") as f:
    content = f.read()

# Just put it directly inside __init__ before self._load_data()
new_init = """    def __init__(self, data_dir: Path):
        import threading
        self.lock = threading.Lock()
        self.data_dir = data_dir
        self.conn = duckdb.connect(database=':memory:')
        self.data_loaded = False
        self.model_loaded = False
        self.alerts_data = []
        self.model_info = {}
        self.metrics = {}
        self.dq = {}
        self.validation_report = {}
        self.current_dataset_id = None
        self.current_run_id = None
        self.current_artifacts_dir = None
        self._load_data()"""

content = re.sub(r"    def __init__\(self, data_dir: Path\):.*?self\._load_data\(\)", new_init, content, flags=re.DOTALL)

# In _load_data, change hasattr or getattr
content = content.replace("if self.current_artifacts_dir is not None:", "if getattr(self, 'current_artifacts_dir', None) is not None:")

with open("backend/services/data_service.py", "w") as f:
    f.write(content)
