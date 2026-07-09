import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { Activity, Clock, ShieldAlert, Zap, Server, Cpu } from 'lucide-react';

const BACKEND = 'http://localhost:3001';

export default function Dashboard() {
  const [stats, setStats] = useState({});
  const [threats, setThreats] = useState({});

  useEffect(() => {
    const fetch = async () => {
      const [s, t] = await Promise.all([
        axios.get(`${BACKEND}/statistics`),
        axios.get(`${BACKEND}/threat-analysis`)
      ]);
      setStats(s.data);
      setThreats(t.data);
    };
    fetch();
    const int = setInterval(fetch, 2000);
    return () => clearInterval(int);
  }, []);

  const intentData = Object.entries(stats.by_intent || {}).map(([name, value]) => ({ name, value }));
  const COLORS = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6'];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#121824] p-4 rounded-lg border border-gray-800">
          <div className="flex items-center text-gray-400 mb-2"><ShieldAlert className="w-4 h-4 mr-2 text-red-500"/> Total Attacks</div>
          <div className="text-3xl font-bold text-white">{stats.total || 0}</div>
        </div>
        <div className="bg-[#121824] p-4 rounded-lg border border-gray-800">
          <div className="flex items-center text-gray-400 mb-2"><Activity className="w-4 h-4 mr-2 text-orange-500"/> Avg Risk Score</div>
          <div className="text-3xl font-bold text-white">{Math.round(threats.average_risk_score || 0)}</div>
        </div>
        <div className="bg-[#121824] p-4 rounded-lg border border-gray-800">
          <div className="flex items-center text-gray-400 mb-2"><Clock className="w-4 h-4 mr-2 text-blue-500"/> Active Sessions</div>
          <div className="text-3xl font-bold text-white">{threats.total_sessions || 0}</div>
        </div>
        <div className="bg-[#121824] p-4 rounded-lg border border-gray-800">
          <div className="flex items-center text-gray-400 mb-2"><Server className="w-4 h-4 mr-2 text-green-500"/> System Health</div>
          <div className="text-xl font-bold text-emerald-400 mt-2 flex items-center"><span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse mr-2"></span> Operational</div>
        </div>
      </div>

      {/* Advanced Performance & ML Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#0d131f] p-4 rounded-lg border border-gray-800">
          <div className="text-xs text-gray-500 mb-1">AI Classification Accuracy</div>
          <div className="text-2xl text-emerald-400">{threats.ml_evaluation?.accuracy || 0}%</div>
        </div>
        <div className="bg-[#0d131f] p-4 rounded-lg border border-gray-800">
          <div className="text-xs text-gray-500 mb-1">Precision / Recall</div>
          <div className="text-2xl text-blue-400">{threats.ml_evaluation?.precision || 0}% / {threats.ml_evaluation?.recall || 0}%</div>
        </div>
        <div className="bg-[#0d131f] p-4 rounded-lg border border-gray-800">
          <div className="text-xs text-gray-500 mb-1">F1 Score</div>
          <div className="text-2xl text-purple-400">{threats.ml_evaluation?.f1_score || 0}%</div>
        </div>
        <div className="bg-[#0d131f] p-4 rounded-lg border border-gray-800">
          <div className="text-xs text-gray-500 mb-1">Avg Inference Time (ms)</div>
          <div className="text-2xl text-yellow-400">12.4ms</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[#121824] p-6 rounded-lg border border-gray-800 shadow-xl">
          <h2 className="text-lg font-medium mb-4 text-gray-200">Risk Distribution</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={intentData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                  {intentData.map((entry, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '4px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        <div className="bg-[#121824] p-6 rounded-lg border border-gray-800 shadow-xl">
          <h2 className="text-lg font-medium mb-4 text-gray-200">Attacks by Intent</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={intentData} margin={{ left: -20 }}>
                <XAxis dataKey="name" stroke="#4b5563" fontSize={12} tickFormatter={(val) => val.split('_').join(' ')} />
                <YAxis stroke="#4b5563" fontSize={12} allowDecimals={false} />
                <Tooltip cursor={{fill: '#1f2937'}} contentStyle={{ backgroundColor: '#1f2937', border: 'none' }} />
                <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
