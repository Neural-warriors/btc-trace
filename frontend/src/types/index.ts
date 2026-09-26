export interface Alert {
  id?: string;
  alert_id: string;
  entity_id: string;
  entity_type: string;
  risk_score: number;
  confidence_score: number;
  priority_score: number;
  alert_category: string;
  category?: string;
  priority?: string;
  explanation: string;
  top_contributing_features?: any[];
  linked_transactions?: string[];
  linked_wallets?: string[];
  linked_ips?: string[];
  model_name?: string;
  model_version?: string;
  dataset_version?: string;
  created_at?: string;
  caveat?: string;
}

export interface Metric {
  name: string;
  value: number;
  trend?: number;
}

export interface Entity {
  entity_id?: string;
  id?: string;
  entity_type?: string;
  type?: string;
  risk_score: number;
  confidence_score?: number;
  confidence?: number;
  priority?: number | string;
  category?: string;
  explanation?: string;
  reasons?: string[];
  features: any;
  transactions?: string[];
  wallets?: string[];
  ips?: string[];
  linked_transactions?: string[];
  linked_wallets?: string[];
  linked_ips?: string[];
}

export interface GraphData {
  nodes: { id: string; type: string; label?: string; [key: string]: any }[];
  edges: { source: string; target: string; type: string; [key: string]: any }[];
}

export interface SearchResult {
  id: string;
  type: string;
  risk_score: number;
  description?: string;
}

export interface Cluster {
  id: string;
  size: number;
  risk_level: string;
  entities: string[];
}
