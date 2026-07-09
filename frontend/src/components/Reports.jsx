import React, { useState } from 'react';
import axios from 'axios';
import { Download, FileText, FileSpreadsheet } from 'lucide-react';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

const BACKEND = 'http://localhost:3001';

export default function Reports() {
  const [loading, setLoading] = useState(false);

  const downloadCSV = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${BACKEND}/export?format=csv`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      const blob = new Blob([res.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Honeypot_Threat_Report_${new Date().getTime()}.csv`;
      a.click();
    } catch (e) {
      alert(`CSV Export failed: ${e.response?.data?.detail || e.message}`);
    }
    setLoading(false);
  };

  const downloadPDF = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${BACKEND}/export?format=json`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      const doc = new jsPDF();
      doc.setFontSize(18);
      doc.text("Enterprise Threat Intelligence Report", 14, 22);
      doc.setFontSize(11);
      doc.setTextColor(100);
      doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 30);
      
      const bodyData = res.data.map(l => [
        new Date(l.timestamp).toLocaleString(),
        l.attacker_ip,
        l.intent,
        l.mitre_attack,
        l.risk_score
      ]);

      doc.autoTable({
        startY: 40,
        head: [['Time', 'IP Address', 'Intent', 'MITRE ATT&CK', 'Risk']],
        body: bodyData,
      });

      doc.save(`Honeypot_Threat_Report_${new Date().getTime()}.pdf`);
    } catch (e) {
      alert(`PDF Export failed: ${e.response?.data?.detail || e.message}`);
    }
    setLoading(false);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="bg-[#121824] p-8 rounded-lg border border-gray-800 shadow-xl">
        <h2 className="text-2xl font-bold mb-2 text-gray-100 flex items-center">
          <FileText className="w-6 h-6 mr-3 text-blue-500" />
          Export Reports
        </h2>
        <p className="text-gray-400 mb-8">
          Generate cryptographic and immutable reports of all logged attacks. Requires Admin or Analyst permissions.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button onClick={downloadCSV} disabled={loading} className="flex flex-col items-center justify-center p-6 bg-[#0a0f18] hover:bg-[#1a2333] border border-gray-700 rounded-lg transition-colors group">
            <FileSpreadsheet className="w-12 h-12 text-green-500 mb-4 group-hover:scale-110 transition-transform" />
            <span className="text-lg font-medium text-gray-200">Export as CSV</span>
            <span className="text-sm text-gray-500 mt-2 text-center">Raw dataset suitable for external SIEM ingestion and analysis.</span>
          </button>

          <button onClick={downloadPDF} disabled={loading} className="flex flex-col items-center justify-center p-6 bg-[#0a0f18] hover:bg-[#1a2333] border border-gray-700 rounded-lg transition-colors group">
            <Download className="w-12 h-12 text-red-500 mb-4 group-hover:scale-110 transition-transform" />
            <span className="text-lg font-medium text-gray-200">Export as PDF</span>
            <span className="text-sm text-gray-500 mt-2 text-center">Formatted executive summary report with threat analytics.</span>
          </button>
        </div>
      </div>
    </div>
  );
}
