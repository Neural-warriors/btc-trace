import { Alert, Entity, GraphData, SearchResult, Cluster } from '../types';

const BASE_URL = 'http://localhost:8000/api';

async function fetcher<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${url}`, options);
  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }
  return response.json();
}

export const client = {
  getHealth: () => fetcher<{ status: string }>('/health'),
  getMetrics: () => fetcher<any>('/metrics'),
  getAlerts: (params?: any) => fetcher<{alerts: Alert[], total: number}>('/alerts?' + new URLSearchParams(params)),
  getEntity: (id: string) => fetcher<Entity>(`/entities/${id}`),
  getNeighborhood: (id: string) => fetcher<GraphData>(`/entities/${id}/neighborhood`),
  search: (params?: any) => {
    const searchParams = new URLSearchParams();
    if (params?.q) searchParams.set('query', params.q);
    if (params?.query) searchParams.set('query', params.query);
    if (params?.type) searchParams.set('entity_type', params.type);
    return fetcher<{results: SearchResult[], total: number}>('/search?' + searchParams.toString());
  },
  getTimeline: () => fetcher<any>('/timeline'),
  getClusters: () => fetcher<Cluster[]>('/entities/clusters'),
  getDataQuality: () => fetcher<any>('/data-quality'),
  getSystemInfo: () => fetcher<any>('/models'),
  uploadDataset: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetcher<any>('/upload', {
      method: 'POST',
      body: formData,
    });
  },
  checkStatus: (datasetId: string, runId: string) => fetcher<{status: string}>(`/upload/status/${datasetId}/${runId}`)
};
