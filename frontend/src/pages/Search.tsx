import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search as SearchIcon } from 'lucide-react';
import { client } from '../api/client';
import { SearchResult } from '../types';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';

export const Search: React.FC = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [type, setType] = useState('All');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;

    setLoading(true);
    setError(false);
    setHasSearched(true);

    try {
      const data = await client.search({ q: query, type: type === 'All' ? undefined : type });
      setResults(data.results || []);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold text-center mb-8">Search Entities</h2>
      
      <form onSubmit={handleSearch} className="flex gap-4">
        <select 
          value={type} 
          onChange={(e) => setType(e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 outline-none focus:border-blue-500"
        >
          <option>All</option>
          <option>Wallet</option>
          <option>Transaction</option>
          <option>IP</option>
          <option>ASN</option>
          <option>Country</option>
        </select>
        <div className="flex-1 relative">
          <SearchIcon className="absolute left-4 top-3.5 text-slate-500" size={20} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter Wallet Address, TXID, IP..."
            className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-12 pr-4 py-3 outline-none focus:border-blue-500"
          />
        </div>
        <button 
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-medium transition-colors"
        >
          Search
        </button>
      </form>

      <div className="mt-8">
        {loading && <LoadingState />}
        {error && <ErrorState />}
        {!loading && !error && hasSearched && results.length === 0 && (
          <div className="text-center text-slate-400 py-12">No results found.</div>
        )}
        {!loading && !error && results.length > 0 && (
          <div className="space-y-4">
            {results.map((res) => (
              <div 
                key={res.id}
                onClick={() => navigate(`/entity/${res.id}`)}
                className="bg-slate-800 p-4 rounded-lg border border-slate-700 hover:border-blue-500 cursor-pointer transition-colors flex justify-between items-center"
              >
                <div>
                  <h4 className="font-semibold text-blue-400">{res.id}</h4>
                  <p className="text-sm text-slate-400 mt-1">{res.description || `Type: ${res.type}`}</p>
                </div>
                <div className="text-right">
                  <div className="text-sm text-slate-500">Risk Score</div>
                  <div className="font-bold text-lg">{res.risk_score}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
