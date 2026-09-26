import pandas as pd
import numpy as np
import re
from typing import Tuple, Dict, Any

def validate_timestamp(series: pd.Series) -> pd.Series:
    def is_valid_ts(x):
        if pd.isna(x): return False
        try:
            pd.to_datetime(x, utc=True)
            return True
        except:
            return False
    return series.apply(is_valid_ts)

def validate_ip(series: pd.Series) -> pd.Series:
    ip_pattern = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|"
        r"^(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}$", re.IGNORECASE
    )
    def is_valid_ip(x):
        if pd.isna(x): return False
        return bool(ip_pattern.match(str(x)))
    return series.apply(is_valid_ip)

def validate_port(series: pd.Series) -> pd.Series:
    def is_valid_port(x):
        try:
            val = int(x)
            return 0 <= val <= 65535
        except:
            return False
    return series.apply(is_valid_port)

def validate_txid(series: pd.Series) -> pd.Series:
    def is_valid_txid(x):
        if pd.isna(x): return False
        return isinstance(x, str) and len(x) == 64 and all(c in '0123456789abcdefABCDEF' for c in x)
    return series.apply(is_valid_txid)

def validate_amount(series: pd.Series) -> pd.Series:
    def is_valid_amt(x):
        try:
            val = float(x)
            return val >= 0.0
        except:
            return False
    return series.apply(is_valid_amt)

def validate_wallet(series: pd.Series) -> pd.Series:
    # Check simple format constraints for BTC address lists separated by ';'
    def is_valid_wallets(x):
        if pd.isna(x): return False
        addrs = str(x).split(';')
        for addr in addrs:
            if not (addr.startswith('1') or addr.startswith('3') or addr.startswith('bc1')):
                return False
        return True
    return series.apply(is_valid_wallets)

def validate_record(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    # Masks
    ts_mask = validate_timestamp(df['timestamp']) if 'timestamp' in df else pd.Series(True, index=df.index)
    src_ip_mask = validate_ip(df['src_ip']) if 'src_ip' in df else pd.Series(True, index=df.index)
    dst_ip_mask = validate_ip(df['dst_ip']) if 'dst_ip' in df else pd.Series(True, index=df.index)
    txid_mask = validate_txid(df['txid']) if 'txid' in df else pd.Series(True, index=df.index)
    fee_mask = validate_amount(df['fee']) if 'fee' in df else pd.Series(True, index=df.index)
    in_addr_mask = validate_wallet(df['input_addresses']) if 'input_addresses' in df else pd.Series(True, index=df.index)
    
    valid_mask = ts_mask & src_ip_mask & dst_ip_mask & txid_mask & fee_mask & in_addr_mask
    
    valid_df = df[valid_mask].copy()
    quarantine_df = df[~valid_mask].copy()
    
    # Calculate reasons (could be optimized)
    reasons = []
    for idx, row in quarantine_df.iterrows():
        r = []
        if 'timestamp' in df and not ts_mask.loc[idx]: r.append('invalid_timestamp')
        if 'src_ip' in df and not src_ip_mask.loc[idx]: r.append('invalid_src_ip')
        if 'dst_ip' in df and not dst_ip_mask.loc[idx]: r.append('invalid_dst_ip')
        if 'txid' in df and not txid_mask.loc[idx]: r.append('invalid_txid')
        if 'fee' in df and not fee_mask.loc[idx]: r.append('invalid_fee')
        if 'input_addresses' in df and not in_addr_mask.loc[idx]: r.append('invalid_input_addresses')
        reasons.append(','.join(r))
    
    quarantine_df['quarantine_reason'] = reasons

    total = len(df)
    valid_cnt = len(valid_df)
    invalid_cnt = len(quarantine_df)
    
    report = {
        "total": total,
        "valid": valid_cnt,
        "invalid": invalid_cnt,
        "duplicates": int(df.duplicated().sum()),
        "nulls_per_field": df.isnull().sum().to_dict(),
        "invalid_reasons": {
            "timestamp": int((~ts_mask).sum()),
            "src_ip": int((~src_ip_mask).sum()),
            "dst_ip": int((~dst_ip_mask).sum()),
            "txid": int((~txid_mask).sum()),
            "fee": int((~fee_mask).sum()),
            "input_addresses": int((~in_addr_mask).sum())
        }
    }
    
    return valid_df, quarantine_df, report
