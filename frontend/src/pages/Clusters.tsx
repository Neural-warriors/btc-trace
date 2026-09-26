import React, { useEffect, useState } from 'react';
import { useGlobalState } from '../context';
import { client } from '../api/client';
import { Cluster } from '../types';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';

export const Clusters: React.FC = () => {
  const { runId } = useGlobalState();
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    client.getClusters()
      .then(data => {
        setClusters(data);
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, [runId]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState />;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Detected Clusters</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {clusters.length === 0 ? (
          <div className="col-span-full text-center text-slate-400 py-12">Clustering not available in current run.</div>
        ) : (
          clusters.map(cluster => (
            <div key={cluster.id} className="bg-slate-800 p-6 rounded-lg border border-slate-700 hover:border-blue-500 cursor-pointer transition-colors">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-slate-200">Cluster {cluster.id}</h3>
                <span className={`px-2 py-1 rounded text-xs font-semibold text-white ${cluster.risk_level.toLowerCase() === 'high' ? 'bg-red-500' : 'bg-slate-600'}`}>
                  {cluster.risk_level}
                </span>
              </div>
              <p className="text-slate-400 mb-2">Size: <span className="text-slate-200">{cluster.size} entities</span></p>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
