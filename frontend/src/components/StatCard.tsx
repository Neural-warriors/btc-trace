import React from 'react';

interface Props {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: number;
}

export const StatCard: React.FC<Props> = ({ title, value, icon, trend }) => {
  return (
    <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-slate-400">{title}</p>
        <div className="flex items-baseline gap-2 mt-1">
          <h3 className="text-2xl font-bold text-slate-100">{value}</h3>
          {trend !== undefined && (
            <span className={`text-sm ${trend >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
              {trend >= 0 ? '+' : ''}{trend}%
            </span>
          )}
        </div>
      </div>
      <div className="text-slate-400 bg-slate-700 p-3 rounded-lg">
        {icon}
      </div>
    </div>
  );
};
