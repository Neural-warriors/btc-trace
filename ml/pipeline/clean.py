from typing import Union
import json
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

from .ingest import ingest
from .validate import validate_record
from .normalize import normalize_record

@dataclass
class CleanResult:
    total_records: int
    valid_records: int
    quarantine_records: int
    validation_report: dict

def clean_pipeline(input_path: Union[str, Path], output_dir: Union[str, Path]) -> CleanResult:
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    
    # Setup paths
    clean_dir = output_dir / "clean"
    quar_dir = output_dir / "quarantine"
    rep_dir = output_dir.parent / "reports" if output_dir.name == "data" else output_dir / "reports"
    
    clean_dir.mkdir(parents=True, exist_ok=True)
    quar_dir.mkdir(parents=True, exist_ok=True)
    rep_dir.mkdir(parents=True, exist_ok=True)
    
    # Ingest
    df = ingest(input_path)
    
    # Validate
    valid_df, quarantine_df, report = validate_record(df)
    
    # Normalize
    if not valid_df.empty:
        valid_df = normalize_record(valid_df)
        
        # Provenance
        valid_df['ingest_timestamp'] = datetime.utcnow().isoformat() + "Z"
        valid_df['dataset_version'] = '1.0.0'
        valid_df['parser_version'] = '1.0.0'
        
        # Save clean
        clean_path = clean_dir / f"{input_path.stem}_clean.parquet"
        valid_df.to_parquet(clean_path, index=False)
        
    # Save quarantine
    if not quarantine_df.empty:
        quar_path = quar_dir / f"{input_path.stem}_quarantine.parquet"
        # Convert all to string for parquet serialization of dirty data
        quarantine_df = quarantine_df.astype(str)
        quarantine_df.to_parquet(quar_path, index=False)
        
    # Save report
    rep_path = rep_dir / f"{input_path.stem}_validation_report.json"
    with open(rep_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    return CleanResult(
        total_records=report['total'],
        valid_records=report['valid'],
        quarantine_records=report['invalid'],
        validation_report=report
    )
