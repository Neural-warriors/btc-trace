import React from 'react';

interface Props {
  level: string;
}

export const RiskBadge: React.FC<Props> = ({ level }) => {
  let color = 'bg-slate-500';
  const l = level.toLowerCase();
  if (l === 'high') color = 'bg-red-500';
  else if (l === 'medium') color = 'bg-amber-500';
  else if (l === 'low') color = 'bg-emerald-500';

  return (
    <span className={`px-2 py-1 rounded text-xs font-semibold text-white ${color}`}>
      {level.toUpperCase()}
    </span>
  );
};
