import { useGlobalState } from '../context';
import { useNavigate } from 'react-router-dom';
import React, { useState } from 'react';
import { client } from '../api/client';
import { Activity } from 'lucide-react';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';

export const UploadDataset: React.FC = () => {
  const navigate = useNavigate();
  const { setRunId } = useGlobalState();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState />;

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] bg-slate-800 rounded-xl border border-slate-700 p-12 text-center">
      <Activity size={64} className="text-slate-500 mb-6" />
      <h2 className="text-3xl font-bold text-slate-100 mb-4">Upload Dataset</h2>
      <p className="text-slate-400 max-w-md mb-8">
        Upload a CSV dataset to process with the BTC-TRACE engine.
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
                          navigate('/');
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
};
