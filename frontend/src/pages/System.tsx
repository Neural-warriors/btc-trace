import React, { useEffect, useState } from 'react';
import { useGlobalState } from '../context';
import { client } from '../api/client';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';

export const System: React.FC = () => {
  const { runId } = useGlobalState();
  const [systemInfo, setSystemInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    client.getSystemInfo()
      .then(data => {
        setSystemInfo(data);
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, [runId]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState />;
  
  // The API returns the model details directly in systemInfo
  const model = systemInfo || {};
  const metrics = model.metrics || {};
  const hyperparams = model.hyperparameters || {};
  const features = model.feature_names || [];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">System Information</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Pipeline Status</h3>
          <p className="text-emerald-400 font-medium flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 block"></span> Operational
          </p>
        </div>
        
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Model Details</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between border-b border-slate-700 pb-2">
              <span className="text-slate-400">Name</span>
              <span className="font-medium text-slate-200">{model.model_name || 'N/A'}</span>
            </div>
            <div className="flex justify-between border-b border-slate-700 pb-2">
              <span className="text-slate-400">Type</span>
              <span className="font-medium text-slate-200">{model.model_type || 'N/A'}</span>
            </div>
            <div className="flex justify-between border-b border-slate-700 pb-2">
              <span className="text-slate-400">Version</span>
              <span className="font-medium text-slate-200">{model.model_version || 'N/A'}</span>
            </div>
            <div className="flex justify-between border-b border-slate-700 pb-2">
              <span className="text-slate-400">Trained At</span>
              <span className="font-medium text-slate-200">{model.training_date ? new Date(model.training_date).toLocaleString() : 'N/A'}</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Metrics</h3>
          <div className="space-y-2 text-sm">
            {Object.entries(metrics).map(([key, val]) => (
              <React.Fragment key={key}>
                {typeof val === 'object' && val !== null ? (
                  <div className="border-b border-slate-700 pb-2">
                    <div className="text-slate-400 capitalize mb-1">{key.replace(/_/g, ' ')}</div>
                    <div className="pl-4 space-y-1">
                      {Object.entries(val as object).map(([subKey, subVal]) => (
                        <div key={subKey} className="flex justify-between">
                          <span className="text-slate-500">{subKey}</span>
                          <span className="font-medium text-slate-200">
                            {typeof subVal === 'number' ? subVal.toFixed(4) : String(subVal)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex justify-between border-b border-slate-700 pb-2">
                    <span className="text-slate-400 capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className="font-medium text-slate-200">
                      {typeof val === 'number' ? val.toFixed(4) : String(val)}
                    </span>
                  </div>
                )}
              </React.Fragment>
            ))}
            {Object.keys(metrics).length === 0 && <span className="text-slate-500">No metrics available</span>}
          </div>
        </div>
        
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Hyperparameters</h3>
          <div className="space-y-2 text-sm">
            {Object.entries(hyperparams).map(([key, val]) => (
              <div key={key} className="flex justify-between border-b border-slate-700 pb-2">
                <span className="text-slate-400 capitalize">{key.replace(/_/g, ' ')}</span>
                <span className="font-medium text-slate-200">{String(val)}</span>
              </div>
            ))}
            {Object.keys(hyperparams).length === 0 && <span className="text-slate-500">No hyperparameters available</span>}
          </div>
        </div>
        
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Features Used ({features.length})</h3>
          <div className="h-48 overflow-y-auto pr-2 space-y-1 text-sm">
            {features.map((f: string, i: number) => (
              <div key={i} className="bg-slate-700 px-3 py-1 rounded text-slate-300 truncate">
                {f}
              </div>
            ))}
            {features.length === 0 && <span className="text-slate-500">No features specified</span>}
          </div>
        </div>
      </div>
    </div>
  );
};
