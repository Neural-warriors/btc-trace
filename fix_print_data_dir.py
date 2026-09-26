import re

with open("backend/services/data_service.py", "r") as f:
    content = f.read()

replacement = """    def __init__(self, data_dir: Path):
        print(f"INITIALIZING DataService WITH data_dir: {data_dir}")
        self.data_dir = data_dir"""

content = re.sub(r"    def __init__\(self, data_dir: Path\):\n        self\.data_dir = data_dir", replacement, content, flags=re.DOTALL)

with open("backend/services/data_service.py", "w") as f:
    f.write(content)
