import json
import random
import uuid
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any

# Ensure reproducible results
np.random.seed(42)
random.seed(42)

def generate_txid() -> str:
    return uuid.uuid4().hex + uuid.uuid4().hex

def generate_btc_address() -> str:
    # Simplified BTC address generation
    prefixes = ['1', '3', 'bc1']
    prefix = random.choice(prefixes)
    if prefix == 'bc1':
        return prefix + ''.join(random.choices('qpzry9x8gf2tvdw0s3jn54khce6mua7l', k=39))
    else:
        return prefix + ''.join(random.choices('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz', k=33))

def generate_ip() -> str:
    return ".".join(str(random.randint(0, 255)) for _ in range(4))

def generate_asn() -> str:
    return f"AS{random.randint(1000, 99999)}"

def main():
    base_dir = Path(__file__).resolve().parent.parent
    data_raw_dir = base_dir / "data" / "raw"
    data_raw_dir.mkdir(parents=True, exist_ok=True)

    num_transactions = 10000
    start_date = datetime(2024, 9, 1, 0, 0, 0)
    
    unique_wallets = [generate_btc_address() for _ in range(2000)]
    unique_ips = [generate_ip() for _ in range(500)]
    unique_asns = [generate_asn() for _ in range(50)]
    countries = ["US", "DE", "FR", "CN", "RU", "JP", "GB", "NL", "CA", "SG"] + ["BR", "IN", "AU", "KR", "ZA", "IT", "ES", "CH", "SE", "NO", "FI", "DK", "PL", "AT", "IE", "NZ", "IL", "AE", "SA", "TR"]
    script_types = ['P2PKH', 'P2SH', 'P2WPKH', 'P2WSH', 'P2TR']

    data: List[Dict[str, Any]] = []

    for i in range(num_transactions):
        # Time distribution across ~30 days
        seconds_offset = random.randint(0, 30 * 24 * 3600)
        timestamp = start_date + timedelta(seconds=seconds_offset)
        
        is_anomaly = random.random() < 0.05
        
        # Determine number of inputs and outputs
        if is_anomaly:
            # Create a highly anomalous transaction!
            # 1. Massive fan-out or fan-in (structuring)
            if random.random() < 0.5:
                num_in = random.randint(10, 50)
                num_out = 1
            else:
                num_in = 1
                num_out = random.randint(10, 50)
                
            inputs = random.choices(unique_wallets, k=num_in)
            outputs = random.choices(unique_wallets, k=num_out)
            
            # 2. Huge amounts (whale movement / illicit transfer)
            in_amts = [round(random.uniform(100.0, 5000.0), 8) for _ in range(num_in)]
            out_amts = [round(random.uniform(10.0, 500.0), 8) for _ in range(num_out)]
            
            # 3. Abnormal port or dark pool ASN
            if random.random() < 0.7:
                dst_port = random.choice([4444, 6667, 8080, 9050])
            else:
                dst_port = 8333 if random.random() < 0.9 else random.randint(1024, 65535)
            
            # 4. Burst timing (multiple anomalous txs in same exact second)
            # (Handled by the model picking up on dense time clusters in the synthetic distribution)
            
            # Make sure total out doesn't exceed total in for realism
            total_in = sum(in_amts)
            total_out = sum(out_amts)
            if total_out > total_in:
                in_amts[0] += (total_out - total_in + 0.1)
                
            fee = round(sum(in_amts) - sum(out_amts), 8)
            if fee < 0:
                fee = 0.0001
        else:
            num_in = random.randint(1, 5)
            num_out = random.randint(1, 5)

            inputs = random.choices(unique_wallets, k=num_in)
            outputs = random.choices(unique_wallets, k=num_out)
            
            # Amounts
            in_amts = [round(random.uniform(0.001, 50.0), 8) for _ in range(num_in)]
            # make out slightly less for fee
            total_in = sum(in_amts)
            out_amts = []
            remaining = total_in * 0.99
            for _ in range(num_out - 1):
                amt = random.uniform(0.001, remaining * 0.5)
                out_amts.append(round(amt, 8))
                remaining -= amt
            out_amts.append(round(remaining, 8))
            
        fee = max(0.0, sum(in_amts) - sum(out_amts))
        
        record = {
            "timestamp": timestamp.isoformat() + "Z",
            "src_ip": random.choice(unique_ips),
            "dst_ip": random.choice(unique_ips),
            "src_port": random.randint(1024, 65535),
            "dst_port": 8333 if random.random() < 0.9 else random.randint(1024, 65535),
            "txid": generate_txid(),
            "input_addresses": ";".join(inputs),
            "output_addresses": ";".join(outputs),
            "input_amounts": ";".join(map(str, in_amts)),
            "output_amounts": ";".join(map(str, out_amts)),
            "fee": fee,
            "script_type": random.choice(script_types),
            "geo_country": random.choice(countries),
            "asn": random.choice(unique_asns),
            "is_anomaly": is_anomaly
        }
        
        data.append(record)

    df = pd.DataFrame(data)

    # Inject data quality issues
    num_rows = len(df)
    
    # 2% missing values in non-critical fields
    missing_idx = np.random.choice(num_rows, size=int(num_rows * 0.02), replace=False)
    df.loc[missing_idx, 'geo_country'] = np.nan
    
    # 1% malformed IPs
    malformed_ip_idx = np.random.choice(num_rows, size=int(num_rows * 0.01), replace=False)
    df.loc[malformed_ip_idx, 'src_ip'] = "999.999.999.999"
    
    # 0.5% duplicate rows
    duplicate_idx = np.random.choice(num_rows, size=int(num_rows * 0.005), replace=False)
    duplicates = df.iloc[duplicate_idx].copy()
    df = pd.concat([df, duplicates], ignore_index=True)
    
    # 0.5% invalid timestamps
    invalid_ts_idx = np.random.choice(len(df), size=int(len(df) * 0.005), replace=False)
    df.loc[invalid_ts_idx, 'timestamp'] = "invalid_date"
    
    # 0.3% negative amounts
    negative_amt_idx = np.random.choice(len(df), size=int(len(df) * 0.003), replace=False)
    df.loc[negative_amt_idx, 'fee'] = -1.0
    
    # Save CSV
    df.to_csv(data_raw_dir / "transactions.csv", index=False)
    
    # Save JSON
    df.to_json(data_raw_dir / "transactions.json", orient="records", date_format="iso", indent=2)
    
    # Save XML
    root = ET.Element("transactions")
    for _, row in df.iterrows():
        tx_elem = ET.SubElement(root, "transaction")
        for col in df.columns:
            val = row[col]
            child = ET.SubElement(tx_elem, col)
            child.text = str(val) if pd.notna(val) else ""
            
    tree = ET.ElementTree(root)
    tree.write(data_raw_dir / "transactions.xml", encoding="utf-8", xml_declaration=True)

    # Save metadata
    metadata = {
        "num_records": len(df),
        "num_unique_wallets": len(unique_wallets),
        "num_unique_ips": len(unique_ips),
        "num_unique_asns": len(unique_asns),
        "generated_at": datetime.utcnow().isoformat(),
        "seed": 42
    }
    with open(data_raw_dir / "synthetic_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

if __name__ == "__main__":
    main()
