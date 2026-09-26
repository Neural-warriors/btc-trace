import re

with open("backend/services/data_service.py", "r") as f:
    content = f.read()

# I want to print the exception if it fails to see why it fails
replacement = """    def _load_data(self, artifacts_dir: Optional[Path] = None):
        try:
            if artifacts_dir is None:
                if getattr(self, 'current_artifacts_dir', None) is not None:
                    artifacts_dir = self.current_artifacts_dir
                else:
                    artifacts_dir = self.data_dir.parent
                    
            # Load alerts
"""
content = re.sub(r"    def _load_data.*?# Load alerts\n", replacement, content, flags=re.DOTALL)

# Add exception printing at the end
replacement_end = """        except Exception as e:
            print(f"ERROR IN _load_data: {e}")
            self.data_loaded = False"""
content = re.sub(r"        except Exception as e:\n            self\.data_loaded = False", replacement_end, content, flags=re.DOTALL)

with open("backend/services/data_service.py", "w") as f:
    f.write(content)
