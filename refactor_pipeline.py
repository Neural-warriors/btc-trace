import re

with open("scripts/train_models.py", "r") as f:
    content = f.read()

argparse_code = """def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-dir", type=str, required=True)
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    artifacts_dir = Path(args.artifacts_dir)
    
    # We will look for splits inside artifacts_dir/splits
    data_dir = artifacts_dir
    models_dir = artifacts_dir / "models"
    reports_dir = artifacts_dir / "reports"
    outputs_dir = artifacts_dir / "outputs"
    
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)"""

idx = content.find("def main() -> None:")
if idx != -1:
    end_setup = content.find("train_path = data_dir / \"splits\"")
    if end_setup != -1:
        content = content[:idx] + argparse_code + "\n\n    # ── 1. Load training data ────────────────────────────────────────\n    " + content[end_setup:]

with open("scripts/train_models.py", "w") as f:
    f.write(content)
