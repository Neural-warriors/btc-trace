import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { client } from '../api/client';
import { Entity } from '../types';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { RiskBadge } from '../components/RiskBadge';

export const EntityDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [entity, setEntity] = useState<Entity | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!id) return;
    client.getEntity(id)
      .then(data => {
        setEntity(data);
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, [id]);

  if (loading) return <LoadingState />;
  if (error || !entity) return <ErrorState message="Entity not found." />;

  const getRiskLevel = (score: number) => {
    if (score >= 0.55) return 'High';
    if (score >= 0.45) return 'Medium';
    return 'Low';
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold break-all">{entity.entity_id || entity.id}</h2>
            <p className="text-slate-400 mt-1">Type: {entity.entity_type || entity.type}</p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <RiskBadge level={getRiskLevel(entity.risk_score)} />
            {entity.confidence_score !== undefined && (
              <span className="text-sm text-slate-400">Confidence: {(entity.confidence_score * 100).toFixed(1)}%</span>
            )}
            {entity.priority !== undefined && typeof entity.priority === 'number' && (
              <span className="text-sm text-slate-400">Priority Score: {(entity.priority * 100).toFixed(1)}%</span>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h3 className="text-lg font-semibold mb-4 text-red-400">Why was this flagged?</h3>
          <p className="text-slate-300 leading-relaxed">
            {entity.explanation || 'Based on our models, this entity shows patterns consistent with high-risk behavior.'}
          </p>
        </div>

        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Top Feature Contributions</h3>
          <div className="space-y-2">
            {Array.isArray(entity.features) ? entity.features.map((featObj: any, index: number) => {
              const entries = Object.entries(featObj);
              return entries.map(([key, val]) => {
                let displayVal = String(val);
                if (typeof val === 'number') {
                  displayVal = val > 1000 ? val.toLocaleString(undefined, { maximumFractionDigits: 0 }) 
                             : Number.isInteger(val) ? String(val) 
                             : val.toFixed(4);
                }
                return (
                  <div key={`${index}-${key}`} className="flex justify-between border-b border-slate-700 pb-2">
                    <span className="text-slate-400 capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className="font-medium text-amber-400">{displayVal}</span>
                  </div>
                );
              });
            }) : (
              <p className="text-slate-500">No feature data available.</p>
            )}
          </div>
        </div>
      </div>

      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
        <h3 className="text-lg font-semibold mb-4">Supporting Evidence</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-900 p-4 rounded-lg">
            <h4 className="text-slate-400 mb-2 font-medium">Related Wallets</h4>
            {entity.wallets && entity.wallets.length > 0 ? (
              <ul className="text-sm space-y-1">
                {entity.wallets.map((w: string, i: number) => (
                  <li key={i} className="text-blue-400 break-all">{w}</li>
                ))}
              </ul>
            ) : <span className="text-slate-600 text-sm">None identified</span>}
          </div>
          <div className="bg-slate-900 p-4 rounded-lg">
            <h4 className="text-slate-400 mb-2 font-medium">Related IPs</h4>
            {entity.ips && entity.ips.length > 0 ? (
              <ul className="text-sm space-y-1">
                {entity.ips.map((ip: string, i: number) => (
                  <li key={i} className="text-blue-400">{ip}</li>
                ))}
              </ul>
            ) : <span className="text-slate-600 text-sm">None identified</span>}
          </div>
          <div className="bg-slate-900 p-4 rounded-lg">
            <h4 className="text-slate-400 mb-2 font-medium">Related Transactions</h4>
            {entity.transactions && entity.transactions.length > 0 ? (
              <ul className="text-sm space-y-1">
                {entity.transactions.map((tx: string, i: number) => (
                  <li key={i} className="text-blue-400 break-all">{tx.substring(0, 16)}...</li>
                ))}
              </ul>
            ) : <span className="text-slate-600 text-sm">None identified</span>}
          </div>
        </div>
      </div>
    </div>
  );
};
