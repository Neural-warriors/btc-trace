import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Union, Optional

def detect_format(filepath: Union[str, Path]) -> str:
    path = Path(filepath)
    ext = path.suffix.lower()
    if ext == '.csv': return 'csv'
    if ext == '.json': return 'json'
    if ext == '.xml': return 'xml'
    raise ValueError(f"Unsupported file format: {ext}")

def load_csv(filepath: Union[str, Path]) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    return df

def load_json(filepath: Union[str, Path]) -> pd.DataFrame:
    df = pd.read_json(filepath, orient='records')
    return df

def load_xml(filepath: Union[str, Path]) -> pd.DataFrame:
    tree = ET.parse(filepath)
    root = tree.getroot()
    data = []
    for child in root:
        record = {}
        for subchild in child:
            record[subchild.tag] = subchild.text
        data.append(record)
    return pd.DataFrame(data)

def ingest(filepath: Union[str, Path]) -> pd.DataFrame:
    path = Path(filepath)
    fmt = detect_format(path)
    
    if fmt == 'csv':
        df = load_csv(path)
    elif fmt == 'json':
        df = load_json(path)
    elif fmt == 'xml':
        df = load_xml(path)
    else:
        raise ValueError("Unknown format")
        
    df['source_file'] = path.name
    df['original_row_number'] = range(1, len(df) + 1)
    
    return df
