import pandas as pd

def normalize_timestamp(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True)

def normalize_ip(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower()

def normalize_port(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors='coerce').fillna(0).astype(int)

def normalize_txid(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower()

def normalize_amount(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors='coerce').round(8)

def normalize_wallet(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip()

def normalize_geo(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.upper()

def normalize_asn(series: pd.Series) -> pd.Series:
    def fmt_asn(x):
        s = str(x).strip().upper()
        if pd.isna(x) or x == 'NAN': return 'UNKNOWN'
        if not s.startswith('AS'):
            return f"AS{s}"
        return s
    return series.apply(fmt_asn)

def normalize_record(df: pd.DataFrame) -> pd.DataFrame:
    df_norm = df.copy()
    if 'timestamp' in df_norm: df_norm['timestamp'] = normalize_timestamp(df_norm['timestamp'])
    if 'src_ip' in df_norm: df_norm['src_ip'] = normalize_ip(df_norm['src_ip'])
    if 'dst_ip' in df_norm: df_norm['dst_ip'] = normalize_ip(df_norm['dst_ip'])
    if 'src_port' in df_norm: df_norm['src_port'] = normalize_port(df_norm['src_port'])
    if 'dst_port' in df_norm: df_norm['dst_port'] = normalize_port(df_norm['dst_port'])
    if 'txid' in df_norm: df_norm['txid'] = normalize_txid(df_norm['txid'])
    if 'fee' in df_norm: df_norm['fee'] = normalize_amount(df_norm['fee'])
    if 'input_addresses' in df_norm: df_norm['input_addresses'] = normalize_wallet(df_norm['input_addresses'])
    if 'output_addresses' in df_norm: df_norm['output_addresses'] = normalize_wallet(df_norm['output_addresses'])
    if 'geo_country' in df_norm: df_norm['geo_country'] = normalize_geo(df_norm['geo_country'])
    if 'asn' in df_norm: df_norm['asn'] = normalize_asn(df_norm['asn'])
    
    return df_norm
