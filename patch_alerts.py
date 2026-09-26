import json
from pathlib import Path
from ml.scoring.explainer import AlertExplainer

data_dir = Path("data")
with open(data_dir / "artifacts" / "active_run.json") as f:
    active = json.load(f)
    
artifacts_dir = data_dir / "artifacts" / active["dataset_id"] / active["run_id"]
alerts_file = artifacts_dir / "outputs" / "alerts.json"

with open(alerts_file) as f:
    alerts_data = json.load(f)
    
explainer = AlertExplainer()

class DummyAlert:
    pass

for alert_dict in alerts_data:
    obj = DummyAlert()
    obj.alert_category = alert_dict.get("category", alert_dict.get("alert_category", ""))
    obj.entity_type = alert_dict.get("entity_type", "transaction")
    obj.entity_id = alert_dict.get("entity_id", "")
    obj.risk_score = alert_dict.get("risk_score", 0.0)
    obj.top_contributing_features = alert_dict.get("top_contributing_features", alert_dict.get("features", []))
    
    alert_dict["explanation"] = explainer.explain(obj)

with open(alerts_file, "w") as f:
    json.dump(alerts_data, f, indent=2)

print("Alerts patched again!")
