import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const BACKEND = 'http://localhost:3001';

export default function ThreatAnalytics() {
  const [stats, setStats] = useState({});
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const fetch = async () => {
      const [s, l] = await Promise.all([
        axios.get(`${BACKEND}/statistics`),
        axios.get(`${BACKEND}/attack-history?limit=20`)
      ]);
      setStats(s.data);
      setLogs(l.data);
    };
    fetch();
    const int = setInterval(fetch, 2000);
    return () => clearInterval(int);
  }, []);

  const mitreData = Object.entries(stats.mitre || {}).map(([name, value]) => ({ name: name.split(' - ')[0], full: name, value }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6">
        
        {/* MITRE ATT&CK */}
        <div className="bg-[#121824] p-6 rounded-lg border border-gray-800 shadow-xl">
          <h2 className="text-lg font-medium mb-4 text-gray-200">MITRE ATT&CK Tactics</h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={mitreData} layout="vertical" margin={{ top: 0, right: 0, left: 40, bottom: 0 }}>
                <XAxis type="number" stroke="#4b5563" />
                <YAxis dataKey="name" type="category" stroke="#9ca3af" fontSize={11} width={60} />
                <Tooltip cursor={{fill: '#1f2937'}} contentStyle={{ backgroundColor: '#1f2937', border: 'none' }} labelFormatter={(val) => mitreData.find(m => m.name === val)?.full} />
                <Bar dataKey="value" fill="#f59e0b" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Session Replay / Timeline */}
      <div className="bg-[#121824] p-6 rounded-lg border border-gray-800 shadow-xl">
        <h2 className="text-lg font-medium mb-4 text-gray-200">Live Attack Timeline & Session Replay</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-400">
            <thead className="bg-[#0a0f18] text-gray-300">
              <tr>
                <th className="p-3 rounded-tl">Time</th>
                <th className="p-3">IP Address (Country)</th>
                <th className="p-3">Target Service</th>
                <th className="p-3">MITRE ATT&CK</th>
                <th className="p-3">Risk</th>
                <th className="p-3 rounded-tr">Blockchain Hash</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log, i) => (
                <tr key={i} className="border-b border-gray-800 hover:bg-[#1a2333] transition-colors">
                  <td className="p-3">{new Date(log.timestamp).toLocaleTimeString()}</td>
                  <td className="p-3 font-mono">{log.attacker_ip} <span className="text-xs text-gray-500">({log.country})</span></td>
                  <td className="p-3">
                    <span className="px-2 py-1 bg-gray-800 rounded text-blue-400 border border-gray-700">{log.service}:{log.port}</span>
                  </td>
                  <td className="p-3 text-orange-400">{log.mitre_attack}</td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded text-white ${log.risk_score > 80 ? 'bg-red-900/50 text-red-400' : 'bg-orange-900/50 text-orange-400'}`}>
                      {log.risk_score}
                    </span>
                  </td>
                  <td className="p-3 font-mono text-xs text-emerald-500 truncate max-w-[200px]">{log.hash}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
