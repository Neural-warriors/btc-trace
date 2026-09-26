import React, { useEffect, useState } from 'react';
import { useGlobalState } from '../context';
import { client } from '../api/client';
import { LoadingState } from '../components/LoadingState';

export const DataQuality: React.FC = () => {
  const { runId } = useGlobalState();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client.getDataQuality()
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [runId]);

  if (loading) return <LoadingState />;

  if (!data || data.total_records === 0) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold">Data Quality Report</h2>
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-12 text-center text-slate-400">
          No data quality report available. Upload a dataset first.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Data Quality Report</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <p className="text-sm text-slate-400">Total Records</p>
          <p className="text-2xl font-bold text-slate-100">{data.total_records?.toLocaleString()}</p>
        </div>
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <p className="text-sm text-slate-400">Training Split</p>
          <p className="text-2xl font-bold text-blue-400">{data.train_records?.toLocaleString()}</p>
        </div>
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <p className="text-sm text-slate-400">Validation Split</p>
          <p className="text-2xl font-bold text-amber-400">{data.validation_records?.toLocaleString()}</p>
        </div>
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <p className="text-sm text-slate-400">Test Split</p>
          <p className="text-2xl font-bold text-emerald-400">{data.test_records?.toLocaleString()}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Feature Engineering</h3>
          <div className="space-y-2">
            <div className="flex justify-between border-b border-slate-700 pb-2">
              <span className="text-slate-400">Total Features</span>
              <span className="font-medium">{data.feature_count}</span>
            </div>
            <div className="flex justify-between border-b border-slate-700 pb-2">
              <span className="text-slate-400">Generated At</span>
              <span className="font-medium text-sm">{data.generated_at ? new Date(data.generated_at).toLocaleString() : 'N/A'}</span>
            </div>
          </div>
        </div>
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Data Splits</h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-400">Train</span>
                <span>{data.train_records} ({((data.train_records / data.total_records) * 100).toFixed(1)}%)</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${(data.train_records / data.total_records) * 100}%` }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-400">Validation</span>
                <span>{data.validation_records} ({((data.validation_records / data.total_records) * 100).toFixed(1)}%)</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div className="bg-amber-500 h-2 rounded-full" style={{ width: `${(data.validation_records / data.total_records) * 100}%` }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-400">Test</span>
                <span>{data.test_records} ({((data.test_records / data.total_records) * 100).toFixed(1)}%)</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${(data.test_records / data.total_records) * 100}%` }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
