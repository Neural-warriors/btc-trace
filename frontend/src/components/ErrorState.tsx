import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props {
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<Props> = ({ message = 'An error occurred.', onRetry }) => (
  <div className="flex flex-col items-center justify-center w-full h-full min-h-[200px] text-slate-400">
    <AlertTriangle size={48} className="text-red-500 mb-4" />
    <p className="mb-4">{message}</p>
    {onRetry && (
      <button onClick={onRetry} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md">
        Retry
      </button>
    )}
  </div>
);
