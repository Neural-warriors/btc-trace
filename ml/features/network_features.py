import pandas as pd

def extract_network_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract network/IP features."""
    features = pd.DataFrame(index=df.index)
    
    features['unique_asn_count'] = 1  # placeholder based on actual ASN data
    features['unique_country_count'] = 1
    
    if 'dst_port' in df.columns:
        features['port_diversity'] = df.groupby('src_ip')['dst_port'].transform('nunique') if 'src_ip' in df.columns else 1
        features['is_standard_port'] = (df['dst_port'] == 8333).astype(int)
    else:
        features['port_diversity'] = 1
        features['is_standard_port'] = 1
        
    if 'src_ip' in df.columns:
        features['ip_tx_count'] = df.groupby('src_ip')['src_ip'].transform('count')
    else:
        features['ip_tx_count'] = 1
        
    return features
