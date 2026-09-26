import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Bell, Search, GitGraph, Clock, Database, Settings, Upload } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    { to: '/', icon: <LayoutDashboard size={20} />, label: 'Overview' },
    { to: '/alerts', icon: <Bell size={20} />, label: 'Alerts' },
    { to: '/search', icon: <Search size={20} />, label: 'Search' },
    { to: '/graph', icon: <GitGraph size={20} />, label: 'Graph Explorer' },
    { to: '/timeline', icon: <Clock size={20} />, label: 'Timeline' },
    { to: '/data-quality', icon: <Database size={20} />, label: 'Data Quality' },
    { to: '/system', icon: <Settings size={20} />, label: 'System' },
    { to: '/upload', icon: <Upload size={20} />, label: 'Upload Dataset' },
  ];

  return (
    <div className="w-64 bg-slate-800 h-screen fixed flex flex-col border-r border-slate-700">
      <div className="p-6 border-b border-slate-700">
        <h1 className="text-xl font-bold text-blue-500">BTC-TRACE</h1>
      </div>
      <nav className="flex-1 py-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-6 py-3 transition-colors ${
                isActive ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-100 hover:bg-slate-700'
              }`
            }
          >
            {item.icon}
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
};
