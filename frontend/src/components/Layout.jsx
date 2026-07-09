import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { Shield, Activity, Map, FileText, LogOut } from 'lucide-react';

export default function Layout({ setToken, role }) {
  const location = useLocation();
  const tabs = [
    { path: '/', name: 'Dashboard', icon: <Activity className="w-4 h-4 mr-2" /> },
    { path: '/analytics', name: 'Threat Analytics (MITRE)', icon: <Map className="w-4 h-4 mr-2" /> },
    { path: '/reports', name: 'Exports & Reports', icon: <FileText className="w-4 h-4 mr-2" /> }
  ];

  return (
    <div className="min-h-screen bg-[#0a0f18] text-gray-100 font-sans flex flex-col">
      <nav className="bg-[#121824] border-b border-gray-800 p-4 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center">
            <Shield className="w-6 h-6 text-blue-500 mr-2" />
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
              Enterprise Command Center
            </h1>
            <span className="ml-4 px-2 py-1 bg-gray-800 text-xs rounded text-gray-400 border border-gray-700">
              Role: {role}
            </span>
          </div>
          <div className="flex space-x-2">
            {tabs.map(t => (
              <Link key={t.path} to={t.path} className={`flex items-center px-4 py-2 rounded-md transition-all text-sm font-medium ${location.pathname === t.path ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-800'}`}>
                {t.icon}{t.name}
              </Link>
            ))}
            <button onClick={() => setToken(null)} className="flex items-center px-4 py-2 rounded-md text-red-400 hover:bg-gray-800 transition-all text-sm font-medium ml-4">
              <LogOut className="w-4 h-4 mr-2" /> Logout
            </button>
          </div>
        </div>
      </nav>
      <main className="flex-1 max-w-7xl mx-auto w-full p-6">
        <Outlet />
      </main>
    </div>
  );
}
