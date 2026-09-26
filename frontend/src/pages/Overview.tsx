import React, { useEffect, useState } from 'react';
import { useGlobalState } from '../context';
import { Activity, Wallet, Network, Bell } from 'lucide-react';
import { StatCard } from '../components/StatCard';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { client } from '../api/client';
import { Alert } from '../types';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';

export const Overview: React.FC = () => {
  const { runId, setRunId } = useGlobalState();
  const [metrics, setMetrics] = useState<any>({});
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    Promise.all([client.getMetrics(), client.getAlerts({ page_size: 5 })])
      .then(([m, a]) => {
        setMetrics(m);
        setAlerts(a.alerts);
        setLoading(false);
      })
      .catch((e) => {
        console.error("Overview error", e);
        setError(true);
        setLoading(false);
      });
  }, [runId]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState />;

  const findMetric = (name: string) => metrics[name] || 0;

  if (Object.keys(metrics).length === 0) {
    return <LoadingState />;
  }

  if (findMetric('total_transactions') === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] bg-slate-800 rounded-xl border border-slate-700 p-12 text-center">
        <Activity size={64} className="text-slate-500 mb-6" />
        <h2 className="text-3xl font-bold text-slate-100 mb-4">No Dataset Loaded</h2>
        <p className="text-slate-400 max-w-md mb-8">
          The SIH Bitcoin Transaction dataset is not currently loaded in memory. You must upload data into the engine before the dashboard can visualize entities, graphs, or ML alerts.
        </p>
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative overflow-hidden w-full max-w-md mx-auto">
            <div className="border-2 border-dashed border-slate-600 rounded-lg p-8 hover:bg-slate-700 transition-colors cursor-pointer bg-slate-800">
              <h3 className="text-lg font-medium text-slate-200 mb-2">Upload CSV Dataset</h3>
              <p className="text-sm text-slate-400 mb-4">Drag and drop or click to select</p>
              <input 
                type="file" 
                className="absolute inset-0 opacity-0 cursor-pointer" 
                accept=".csv"
                onChange={async (e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    setLoading(true);
                    try {
                      const res = await client.uploadDataset(e.target.files[0]);
                      const datasetId = res.dataset_id;
                      const runId = res.run_id;
                      
                      const pollStatus = async () => {
                        try {
                          const statusRes = await client.checkStatus(datasetId, runId);
                          if (statusRes.status === 'ready') {
                            setRunId(runId);
                          } else if (statusRes.status === 'failed') {
                            setError(true);
                            setLoading(false);
                            alert("Processing failed on the backend.");
                          } else {
                            setTimeout(pollStatus, 2000);
                          }
                        } catch(err) {
                          setTimeout(pollStatus, 2000);
                        }
                      };
                      
                      setTimeout(pollStatus, 2000);
                      
                    } catch(err) {
                      console.error("Upload error", err);
                      setError(true);
                      setLoading(false);
                    }
                  }
                }}
              />
            </div>
          </div>
        </div>
      </div>
    );
  }

  const timelineData = metrics.timeline_data || [];
  const chartData = timelineData.map((d: any) => ({
    name: d.date ? d.date.substring(5, 10) : '',  // Show MM-DD
    value: d.count || 0
  }));

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Dashboard Overview</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Total Transactions" value={findMetric('total_transactions')} icon={<Activity size={24} />} />
        <StatCard title="Total Wallets" value={findMetric('total_wallets')} icon={<Wallet size={24} />} />
        <StatCard title="Total IPs" value={findMetric('total_ips')} icon={<Network size={24} />} />
        <StatCard title="Total Alerts" value={findMetric('total_alerts')} icon={<Bell size={24} />} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="High Risk" value={findMetric('high_risk_count')} icon={<Activity size={24} />} />
        <StatCard title="Medium Risk" value={findMetric('medium_risk_count')} icon={<Activity size={24} />} />
        <StatCard title="Low Risk" value={findMetric('low_risk_count')} icon={<Activity size={24} />} />
        <StatCard 
          title="Model Status" 
          value={findMetric('model_accuracy') > 0 ? `${findMetric('model_accuracy')}% AUC` : 'Unsupervised'} 
          icon={<Activity size={24} />} 
        />
      </div>

      {findMetric('total_asns') > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard title="Total ASNs" value={findMetric('total_asns')} icon={<Network size={24} />} />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Alerts by Category</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', color: '#fff' }} />
                <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Transactions Over Time</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', color: '#fff' }} />
                <Line type="monotone" dataKey="value" stroke="#10b981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
        <h3 className="text-lg font-semibold mb-4">Recent Alerts</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-400">
            <thead className="text-xs uppercase bg-slate-700 text-slate-300">
              <tr>
                <th className="px-4 py-3">Entity</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Risk Score</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-4 text-center">No alerts found</td>
                </tr>
              ) : (
                alerts.map(alert => (
                  <tr key={alert.alert_id || alert.id} className="border-b border-slate-700">
                    <td className="px-4 py-3 font-medium text-slate-200">{alert.entity_id}</td>
                    <td className="px-4 py-3">{alert.entity_type}</td>
                    <td className="px-4 py-3">{alert.alert_category || alert.category}</td>
                    <td className="px-4 py-3">{alert.risk_score}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
