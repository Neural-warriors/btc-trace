import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';

import { Overview } from './pages/Overview';
import { Alerts } from './pages/Alerts';
import { Search } from './pages/Search';
import { EntityDetail } from './pages/EntityDetail';
import { GraphExplorer } from './pages/GraphExplorer';
import { Timeline } from './pages/Timeline';
import { DataQuality } from './pages/DataQuality';
import { System } from './pages/System';
import { UploadDataset } from './pages/Upload';

import { ErrorBoundary } from './components/ErrorBoundary';

const App: React.FC = () => {
  return (
    <div className="flex min-h-screen bg-slate-900 text-slate-200">
      <Sidebar />
      <main className="flex-1 ml-64 p-8 overflow-y-auto">
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/search" element={<Search />} />
            <Route path="/entity/:id" element={<EntityDetail />} />
            <Route path="/graph" element={<GraphExplorer />} />
            <Route path="/timeline" element={<Timeline />} />
            <Route path="/data-quality" element={<DataQuality />} />
            <Route path="/system" element={<System />} />
            <Route path="/upload" element={<UploadDataset />} />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
  );
};

export default App;
