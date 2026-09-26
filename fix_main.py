import re
with open("backend/main.py", "r") as f: content = f.read()
if "router(debug.router" not in content:
    content = content.replace("from .routers import upload, alerts, entities, search, system, transactions", "from .routers import upload, alerts, entities, search, system, transactions, debug")
    content = content.replace("app.include_router(upload.router)", "app.include_router(upload.router)\napp.include_router(debug.router)")
with open("backend/main.py", "w") as f: f.write(content)
