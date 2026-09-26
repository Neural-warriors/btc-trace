import re

with open("backend/services/data_service.py", "r") as f:
    content = f.read()

replacement = """                    "explanation": alert.get("explanation"),
                    "reasons": [f"{k}: {v}" for d in alert.get("top_contributing_features", []) for k, v in d.items()],
                    "features": alert.get("features", {}),"""

content = re.sub(r"                    \"explanation\": alert\.get\(\"explanation\"\),\n                    \"reasons\": alert\.get\(\"top_contributing_features\", \[\]\),\n                    \"features\": alert\.get\(\"features\", \{\}\),", replacement, content, flags=re.DOTALL)

with open("backend/services/data_service.py", "w") as f:
    f.write(content)
