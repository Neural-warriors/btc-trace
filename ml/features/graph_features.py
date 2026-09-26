import pandas as pd
import networkx as nx
import numpy as np

def extract_graph_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract graph-structural features using networkx."""
    if df.empty or 'src_wallet' not in df.columns or 'dst_wallet' not in df.columns:
        return pd.DataFrame(index=df.index)
        
    G = nx.DiGraph()
    
    edges = df[['src_wallet', 'dst_wallet']].dropna().values.tolist()
    G.add_edges_from(edges)
    
    in_degrees = dict(G.in_degree())
    out_degrees = dict(G.out_degree())
    clustering = nx.clustering(nx.Graph(G)) # clustering coeff usually on undirected
    
    try:
        pagerank = nx.pagerank(G, alpha=0.85)
    except Exception:
        pagerank = {n: 0.0 for n in G.nodes()}
        
    components = list(nx.weakly_connected_components(G))
    comp_size = {node: len(c) for c in components for node in c}
    
    # Map back to transactions
    features = pd.DataFrame(index=df.index)
    features['src_in_degree'] = df['src_wallet'].map(in_degrees).fillna(0)
    features['src_out_degree'] = df['src_wallet'].map(out_degrees).fillna(0)
    features['dst_in_degree'] = df['dst_wallet'].map(in_degrees).fillna(0)
    features['dst_out_degree'] = df['dst_wallet'].map(out_degrees).fillna(0)
    
    features['src_clustering'] = df['src_wallet'].map(clustering).fillna(0)
    features['dst_clustering'] = df['dst_wallet'].map(clustering).fillna(0)
    
    features['src_pagerank'] = df['src_wallet'].map(pagerank).fillna(0)
    features['dst_pagerank'] = df['dst_wallet'].map(pagerank).fillna(0)
    
    features['src_comp_size'] = df['src_wallet'].map(comp_size).fillna(0)
    
    return features
