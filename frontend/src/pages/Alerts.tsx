import React, { useEffect, useState } from 'react';
import { useGlobalState } from '../context';
import { useNavigate } from 'react-router-dom';
import { client } from '../api/client';
import { Alert } from '../types';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { RiskBadge } from '../components/RiskBadge';
import { Copy } from 'lucide-react';

export const Alerts: React.FC = () => {
  const { runId } = useGlobalState();
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [entityTypeFilter, setEntityTypeFilter] = useState<string>('transaction');
  const [sortOrder, setSortOrder] = useState<string>('risk_desc');

  useEffect(() => {
    setLoading(true);
    const params: any = { page_size: 5000 };
    if (entityTypeFilter !== 'all') {
      params.entity_type = entityTypeFilter;
    }
    
    client.getAlerts(params)
      .then(data => {
        let fetchedAlerts = data.alerts;
        if (sortOrder === 'risk_asc') {
          fetchedAlerts.sort((a, b) => a.risk_score - b.risk_score);
        } else if (sortOrder === 'risk_desc') {
          fetchedAlerts.sort((a, b) => b.risk_score - a.risk_score);
        }
        setAlerts(fetchedAlerts);
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, [runId, entityTypeFilter, sortOrder]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState />;

  const getRiskLevel = (score: number) => {
    if (score >= 0.55) return 'High';
    if (score >= 0.45) return 'Medium';
    return 'Low';
  };

  const handleCopy = (e: React.MouseEvent, text: string) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Alerts</h2>
        <div className="flex gap-4">
          <select 
            value={entityTypeFilter} 
            onChange={(e) => setEntityTypeFilter(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded p-2 text-sm"
          >
            <option value="all">All Entity Types</option>
            <option value="transaction">Transaction</option>
            <option value="wallet">Wallet</option>
            <option value="ip">IP Address</option>
            <option value="asn">ASN</option>
            <option value="country">Country</option>
          </select>
          <select 
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded p-2 text-sm"
          >
            <option value="risk_desc">Sort by Risk (High to Low)</option>
            <option value="risk_asc">Sort by Risk (Low to High)</option>
          </select>
        </div>
      </div>

      <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
        <table className="w-full text-left text-sm text-slate-400">
          <thead className="text-xs uppercase bg-slate-700 text-slate-300">
            <tr>
              <th className="px-6 py-4">Priority</th>
              <th className="px-6 py-4">Entity</th>
              <th className="px-6 py-4">Type</th>
              <th className="px-6 py-4">Risk Level</th>
              <th className="px-6 py-4">Category</th>
              <th className="px-6 py-4">Explanation</th>
            </tr>
          </thead>
          <tbody>
            {alerts.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center">No alerts found.</td>
              </tr>
            ) : (
              alerts.map(alert => (
                <tr 
                  key={alert.id || alert.alert_id} 
                  className="border-b border-slate-700 hover:bg-slate-700 cursor-pointer transition-colors"
                  onClick={() => navigate(`/entity/${alert.entity_id}`)}
                >
                  <td className="px-6 py-4 font-medium text-slate-200">{(alert.priority_score * 100).toFixed(1)}</td>
                  <td className="px-6 py-4 flex items-center gap-2">
                    <span className="text-blue-400 font-mono">
                      {alert.entity_id.substring(0, 12)}...
                    </span>
                    <button 
                      onClick={(e) => handleCopy(e, alert.entity_id)}
                      className="p-1 text-slate-500 hover:text-slate-300 transition-colors"
                      title="Copy full ID"
                    >
                      <Copy size={14} />
                    </button>
                  </td>
                  <td className="px-6 py-4 capitalize">{alert.entity_type}</td>
                  <td className="px-6 py-4">
                    <RiskBadge level={getRiskLevel(alert.risk_score)} />
                  </td>
                  <td className="px-6 py-4">{alert.category || alert.alert_category || 'Anomaly'}</td>
                  <td className="px-6 py-4 truncate max-w-xs">{alert.explanation || 'Unsupervised anomaly detection flagged this entity.'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
