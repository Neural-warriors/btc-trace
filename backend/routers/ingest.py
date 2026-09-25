from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
import subprocess
import shutil
import time
from pathlib import Path
from ..services import data_service
from ..models.schemas import IngestResponse

router = APIRouter(tags=["Ingestion"])

@router.post("/load-demo")
def load_demo_data(background_tasks: BackgroundTasks):
    """
    Generate demo data, train models, and reload.
    """
    def run_pipeline():
        try:
            # Run the generate, ingest, and train steps
            project_dir = Path(__file__).parent.parent.parent
            subprocess.run(["make", "ingest"], cwd=str(project_dir), check=True)
            subprocess.run(["make", "train"], cwd=str(project_dir), check=True)
            if data_service:
                data_service.data_service._load_data()
        except Exception as e:
            print(f"Error loading demo data: {e}")
            
    background_tasks.add_task(run_pipeline)
    return {"message": "Demo data generation and training started in background."}

@router.post("/ingest")
def ingest_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Upload a CSV/JSON/XML file, clean it, train the model, and score.
    """
    def process_file(file_path: Path):
        try:
            project_dir = Path(__file__).parent.parent.parent
            # Here we could call a specific python script or we can just replace the raw transactions file and run the pipeline
            raw_dir = project_dir / "data" / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            dest = raw_dir / "transactions.csv"
            
            # Just move the uploaded file there
            shutil.move(str(file_path), str(dest))
            
            # Run the data pipeline
            subprocess.run(["python3", "ml/pipeline/clean.py", "data/raw/transactions.csv", "data/clean/transactions_clean.parquet"], cwd=str(project_dir), check=True)
            subprocess.run(["make", "train"], cwd=str(project_dir), check=True)
            if data_service:
                data_service.data_service._load_data()
        except Exception as e:
            print(f"Error processing upload: {e}")

    # Save uploaded file temporarily
    temp_file = Path(f"/tmp/{file.filename}_{time.time()}")
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    background_tasks.add_task(process_file, temp_file)
    return {"message": "File upload received. Processing started in background."}

@router.get("/download-sample/csv")
def download_sample_csv():
    """
    Download a sample valid CSV for the user to look at.
    """
    project_dir = Path(__file__).parent.parent.parent
    sample_file = project_dir / "testing_data.csv"
    if not sample_file.exists():
        # Fallback to generating one or returning raw
        sample_file = project_dir / "data" / "raw" / "transactions.csv"
        
    if not sample_file.exists():
        raise HTTPException(status_code=404, detail="No sample file available.")
        
    return FileResponse(
        path=str(sample_file),
        filename="btc_trace_sample.csv",
        media_type="text/csv"
    )
