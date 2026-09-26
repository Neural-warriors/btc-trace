import re

with open("backend/services/data_service.py", "r") as f:
    content = f.read()

replacement = """            if artifacts_dir is None:
                if getattr(self, 'current_artifacts_dir', None) is not None:
                    artifacts_dir = self.current_artifacts_dir
                else:
                    artifacts_dir = self.data_dir.parent
                    
            print(f"LOADING DATA FROM: {artifacts_dir}")
            # Load alerts"""

content = re.sub(r"            if artifacts_dir is None.*?# Load alerts", replacement, content, flags=re.DOTALL)

with open("backend/services/data_service.py", "w") as f:
    f.write(content)
