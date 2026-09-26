import pandas as pd
import numpy as np

def extract_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract temporal features from transaction data."""
    features = pd.DataFrame(index=df.index)
    
    if 'timestamp' not in df.columns:
        return features
        
    dt = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
    
    features['hour_of_day'] = dt.dt.hour.fillna(0).astype(int)
    features['day_of_week'] = dt.dt.dayofweek.fillna(0).astype(int)
    features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
    features['minutes_since_midnight'] = (dt.dt.hour * 60 + dt.dt.minute).fillna(0).astype(int)
    
    # Sort and compute inter-tx time
    df_sorted = df.copy()
    df_sorted['dt'] = dt
    if 'src_ip' in df_sorted.columns:
        df_sorted = df_sorted.sort_values(by=['src_ip', 'dt'])
        df_sorted['inter_tx_time_seconds'] = df_sorted.groupby('src_ip')['dt'].diff().dt.total_seconds()
        features['inter_tx_time_seconds'] = df_sorted['inter_tx_time_seconds'].fillna(86400) # default 1 day
        features['is_burst'] = (features['inter_tx_time_seconds'] < 60).astype(int)
        
        # rolling counts
        df_sorted.set_index('dt', inplace=True)
        # simplified counting per IP
        features['tx_count_last_1h'] = 1 # placeholder
        features['tx_count_last_24h'] = 1 # placeholder
    else:
        features['inter_tx_time_seconds'] = 86400
        features['is_burst'] = 0
        features['tx_count_last_1h'] = 0
        features['tx_count_last_24h'] = 0
        
    return features
