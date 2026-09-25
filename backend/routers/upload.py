import os
import uuid
import shutil
import subprocess
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from ..services import data_service

router = APIRouter(prefix="/upload", tags=["Upload"])

def process_dataset(filepath: Path, dataset_id: str, run_id: str, artifacts_dir: Path):
    try:
        project_root = filepath.parent.parent.parent.parent.parent.parent
        print(f"Processing uploaded dataset {dataset_id} run {run_id} at {filepath}")
        
        # 1. Run Clean Pipeline
        clean_script = f"python3 -c \"from ml.pipeline.clean import clean_pipeline; from pathlib import Path; clean_pipeline(Path('{filepath}'), Path('{artifacts_dir}'))\""
        subprocess.run(clean_script, shell=True, cwd=project_root, check=True)
        print("Clean pipeline complete.")
        
        # 2. Run Split Pipeline
        split_script = f"python3 -c \"from ml.pipeline.split import temporal_split; from ml.pipeline.id_mapping import EntityMapper; import pandas as pd; from pathlib import Path; df = pd.read_parquet('{artifacts_dir}/clean/{filepath.stem}_clean.parquet'); train, val, test = temporal_split(df, output_dir=Path('{artifacts_dir}/splits')); mapper = EntityMapper(); mapper.build_from_dataframe(df); mapper.save(Path('{artifacts_dir}/clean/entity_mapping.json'))\""
        subprocess.run(split_script, shell=True, cwd=project_root, check=True)
        print("Split pipeline complete.")
        
        # 3. Train Models
        train_script = f"python3 scripts/train_models.py --artifacts-dir {artifacts_dir}"
        subprocess.run(train_script, shell=True, cwd=project_root, check=True)
        print("Model training complete.")
        
        # 4. Reload data in memory
        if data_service.data_service:
            data_service.data_service.set_current_run(dataset_id, run_id, artifacts_dir)
            data_service.data_service._load_data(artifacts_dir)
        print("In-memory dataset reloaded.")
        
        # Write status file
        with open(artifacts_dir / "status.json", "w") as f:
            f.write('{"status": "ready"}')
        
    except subprocess.CalledProcessError as e:
        print(f"Error during dataset processing pipeline: {e}")
        with open(artifacts_dir / "status.json", "w") as f:
            f.write('{"status": "failed"}')

@router.post("")
async def upload_dataset(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    try:
        dataset_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())
        
        project_root = Path(__file__).parent.parent.parent
        artifacts_dir = project_root / "data" / "artifacts" / dataset_id / run_id
        
        data_raw_dir = artifacts_dir / "raw"
        data_raw_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = data_raw_dir / "transactions.csv"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        with open(artifacts_dir / "status.json", "w") as f:
            f.write('{"status": "processing"}')
            
        # Start processing in the background
        background_tasks.add_task(process_dataset, file_path, dataset_id, run_id, artifacts_dir)
        
        return JSONResponse(content={
            "status": "processing_started",
            "message": "Dataset uploaded successfully. Pipeline is running in the background.",
            "filename": file.filename,
            "dataset_id": dataset_id,
            "run_id": run_id
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload dataset: {e}")

@router.get("/status/{dataset_id}/{run_id}")
async def check_status(dataset_id: str, run_id: str):
    project_root = Path(__file__).parent.parent.parent
    status_file = project_root / "data" / "artifacts" / dataset_id / run_id / "status.json"
    
    if not status_file.exists():
        return JSONResponse(content={"status": "not_found"})
        
    import json
    with open(status_file, "r") as f:
        data = json.load(f)
        
    return JSONResponse(content=data)
