import re

with open("backend/services/data_service.py", "r") as f:
    content = f.read()

replacement = """            except Exception as e:
                print(f"FAILED TO LOAD ACTIVE RUN: {e}")
                self._load_data(data_dir.parent)"""

content = re.sub(r"            except:\n                self\._load_data\(data_dir\.parent\)", replacement, content, flags=re.DOTALL)

with open("backend/services/data_service.py", "w") as f:
    f.write(content)
