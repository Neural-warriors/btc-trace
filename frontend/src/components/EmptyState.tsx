import React from 'react';
import { FolderSearch } from 'lucide-react';

interface Props {
  message?: string;
}

export const EmptyState: React.FC<Props> = ({ message = 'No data available.' }) => (
  <div className="flex flex-col items-center justify-center w-full h-full min-h-[200px] text-slate-400">
    <FolderSearch size={48} className="mb-4 text-slate-500" />
    <p>{message}</p>
  </div>
);
