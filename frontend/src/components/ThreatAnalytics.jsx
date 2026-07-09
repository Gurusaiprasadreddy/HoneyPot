import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const BACKEND = 'http://localhost:3001';

export default function ThreatAnalytics() {
  const [stats, setStats] = useState({});
  const [logs, setLogs] = useState([]);

  const [verifying, setVerifying] = useState({});
  const [verified, setVerified] = useState({});

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

  const verifyHash = async (hash) => {
    if (verified[hash]) return;
    setVerifying(prev => ({ ...prev, [hash]: true }));
    try {
      const res = await axios.get(`${BACKEND}/verify/${hash}`);
      if (res.data.verified) {
        setVerified(prev => ({ ...prev, [hash]: true }));
      }
    } catch (e) {
      console.error("Verification failed", e);
    }
    setVerifying(prev => ({ ...prev, [hash]: false }));
  };

  const [generatingReport, setGeneratingReport] = useState({});
  const [aiReport, setAiReport] = useState(null);

  const generateReport = async (ip) => {
    setGeneratingReport(prev => ({ ...prev, [ip]: true }));
    try {
      const res = await axios.get(`${BACKEND}/api/report/${ip}`);
      setAiReport(res.data.report);
    } catch (e) {
      console.error("Report generation failed", e);
      setAiReport("Failed to contact AI engine.");
    }
    setGeneratingReport(prev => ({ ...prev, [ip]: false }));
  };

  const mitreData = Object.entries(stats.mitre || {}).map(([name, value]) => ({ name: name.split(' - ')[0], full: name, value }));

  return (
    <div className="space-y-6">
      
      {/* AI Report Modal */}
      {aiReport && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#0f1520] border border-gray-700 p-6 rounded-lg w-full max-w-3xl shadow-2xl overflow-y-auto max-h-[80vh]">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-blue-400 flex items-center">
                <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                AI Cyber Threat Intelligence Report
              </h2>
              <button onClick={() => setAiReport(null)} className="text-gray-400 hover:text-white">✕</button>
            </div>
            <div className="prose prose-invert max-w-none text-sm text-gray-300">
              <pre className="whitespace-pre-wrap font-sans">{aiReport}</pre>
            </div>
          </div>
        </div>
      )}

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
                <th className="p-3 rounded-tr">Blockchain Verification</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log, i) => (
                <tr key={i} className={`border-b border-gray-800 transition-colors ${log.intent?.includes('[CROSS-SERVICE APT]') ? 'bg-red-900/20 border-red-900/50 hover:bg-red-900/30' : 'hover:bg-[#1a2333]'}`}>
                  <td className="p-3">{new Date(log.timestamp).toLocaleTimeString()}</td>
                  <td className="p-3 font-mono">
                    <div className="flex items-center space-x-2">
                      <span>{log.attacker_ip}</span>
                      <span className="text-xs text-gray-500">({log.country})</span>
                      <button 
                        onClick={() => generateReport(log.attacker_ip)}
                        disabled={generatingReport[log.attacker_ip]}
                        className={`text-xs px-2 py-1 rounded border ${generatingReport[log.attacker_ip] ? 'border-gray-700 text-gray-500' : 'border-blue-700 text-blue-400 hover:bg-blue-900/50'}`}
                      >
                        {generatingReport[log.attacker_ip] ? 'Generating...' : 'AI Report'}
                      </button>
                    </div>
                  </td>
                  <td className="p-3">
                    <span className="px-2 py-1 bg-gray-800 rounded text-blue-400 border border-gray-700">{log.service}:{log.port}</span>
                  </td>
                  <td className="p-3 text-orange-400">{log.mitre_attack}</td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded text-white ${log.risk_score > 80 ? 'bg-red-900/50 text-red-400' : 'bg-orange-900/50 text-orange-400'}`}>
                      {log.risk_score}
                    </span>
                  </td>
                  <td className="p-3 font-mono text-xs max-w-[250px]">
                    {verified[log.hash] ? (
                      <div className="flex items-center text-emerald-400">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        Verified on Blockchain
                      </div>
                    ) : (
                      <button 
                        onClick={() => verifyHash(log.hash)} 
                        disabled={verifying[log.hash]}
                        className={`truncate w-full text-left transition-colors ${verifying[log.hash] ? 'text-gray-500' : 'text-emerald-500 hover:text-emerald-300 hover:underline cursor-pointer'}`}
                        title="Click to Verify Integrity on Ethereum Ledger"
                      >
                        {verifying[log.hash] ? 'Verifying Smart Contract...' : log.hash}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
