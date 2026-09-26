import React, { useEffect, useState } from 'react';
import { useGlobalState } from '../context';
import { client } from '../api/client';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

export const Timeline: React.FC = () => {
  const { runId } = useGlobalState();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    client.getTimeline()
      .then(d => { setData(d); setLoading(false); })
      .catch(() => { setError(true); setLoading(false); });
  }, [runId]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message="Failed to load timeline data." />;
  if (!data || !data.entries || data.entries.length === 0) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold">Timeline Analysis</h2>
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-12 text-center text-slate-400">
          No timeline data available for the current dataset.
        </div>
      </div>
    );
  }

  const chartData = data.entries.map((e: any) => ({
    date: e.date ? e.date.substring(0, 10) : '',
    count: e.count
  }));

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Timeline Analysis</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <p className="text-sm text-slate-400">Time Range Start</p>
          <p className="text-lg font-semibold">{data.time_range_start?.substring(0, 10) || 'N/A'}</p>
        </div>
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <p className="text-sm text-slate-400">Time Range End</p>
          <p className="text-lg font-semibold">{data.time_range_end?.substring(0, 10) || 'N/A'}</p>
        </div>
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <p className="text-sm text-slate-400">Total Days</p>
          <p className="text-lg font-semibold">{chartData.length}</p>
        </div>
      </div>

      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
        <h3 className="text-lg font-semibold mb-4">Daily Transaction Volume</h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <XAxis dataKey="date" stroke="#94a3b8" tick={{fontSize: 11}} angle={-45} textAnchor="end" height={60} />
              <YAxis stroke="#94a3b8" />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', color: '#fff' }} />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
        <h3 className="text-lg font-semibold mb-4">Transaction Activity Trend</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <XAxis dataKey="date" stroke="#94a3b8" tick={{fontSize: 11}} angle={-45} textAnchor="end" height={60} />
              <YAxis stroke="#94a3b8" />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', color: '#fff' }} />
              <Line type="monotone" dataKey="count" stroke="#10b981" strokeWidth={2} dot={{r: 3}} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
        <h3 className="text-lg font-semibold p-6 pb-0">Daily Breakdown</h3>
        <table className="w-full text-left text-sm text-slate-400 mt-4">
          <thead className="text-xs uppercase bg-slate-700 text-slate-300">
            <tr>
              <th className="px-6 py-3">Date</th>
              <th className="px-6 py-3">Transaction Count</th>
            </tr>
          </thead>
          <tbody>
            {chartData.map((row: any, i: number) => (
              <tr key={i} className="border-b border-slate-700">
                <td className="px-6 py-3 font-medium text-slate-200">{row.date}</td>
                <td className="px-6 py-3">{row.count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
