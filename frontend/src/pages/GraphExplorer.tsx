import { useGlobalState } from '../context';
import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import { client } from '../api/client';
import { LoadingState } from '../components/LoadingState';

export const GraphExplorer: React.FC = () => {
  const { runId } = useGlobalState();
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    // Fetch some generic graph data or a specific neighborhood
    client.getNeighborhood('sample')
      .then(data => {
        if (containerRef.current) {
          cyRef.current = cytoscape({
            container: containerRef.current,
            elements: [
              ...data.nodes.map(n => ({ data: { id: n.id, label: n.label || n.id, type: n.type } })),
              ...data.edges.map(e => ({ data: { source: e.source, target: e.target, label: e.type } }))
            ],
            style: [
              {
                selector: 'node',
                style: {
                  'background-color': function(ele: any) {
                    const type = ele.data('type');
                    if (type === 'wallet') return '#10b981';
                    if (type === 'ip') return '#f59e0b';
                    return '#3b82f6';
                  },
                  'label': 'data(label)',
                  'color': '#fff',
                  'text-valign': 'center',
                  'text-halign': 'center',
                  'font-size': '10px'
                }
              },
              {
                selector: 'edge',
                style: {
                  'width': 2,
                  'line-color': '#475569',
                  'target-arrow-color': '#475569',
                  'target-arrow-shape': 'triangle',
                  'curve-style': 'bezier'
                }
              }
            ],
            layout: {
              name: 'concentric',
              minNodeSpacing: 30,
              padding: 10
            }
          });
        }
        setLoading(false);
      })
      .catch(() => {
        // Fallback for demo
        setLoading(false);
      });

    return () => {
      if (cyRef.current) cyRef.current.destroy();
    };
  }, [runId]);

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Graph Explorer</h2>
        <div className="flex gap-2">
          <button onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 1.2)} className="bg-slate-800 px-3 py-1 rounded text-sm hover:bg-slate-700">Zoom In</button>
          <button onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 0.8)} className="bg-slate-800 px-3 py-1 rounded text-sm hover:bg-slate-700">Zoom Out</button>
          <button onClick={() => cyRef.current?.fit()} className="bg-slate-800 px-3 py-1 rounded text-sm hover:bg-slate-700">Fit to Screen</button>
        </div>
      </div>
      <div className="flex-1 bg-slate-800 rounded-lg border border-slate-700 relative overflow-hidden min-h-[600px]">
        {loading && <div className="absolute inset-0 z-10 bg-slate-800/80"><LoadingState /></div>}
        <div ref={containerRef} className="w-full h-full absolute inset-0" />
        <div className="absolute top-4 right-4 bg-slate-900/90 border border-slate-700 p-4 rounded shadow-lg text-sm z-20 backdrop-blur-sm">
          <h4 className="font-semibold text-slate-200 mb-2">Legend</h4>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-3 h-3 rounded-full bg-blue-500"></div>
            <span className="text-slate-300">Transaction</span>
          </div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
            <span className="text-slate-300">Wallet</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-amber-500"></div>
            <span className="text-slate-300">IP Address</span>
          </div>
        </div>
      </div>
    </div>
  );
};
