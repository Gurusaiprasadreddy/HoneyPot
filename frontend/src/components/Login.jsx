import React, { useState } from 'react';
import { Shield } from 'lucide-react';
import axios from 'axios';

const BACKEND = 'http://localhost:3001';

export default function Login({ setToken, setRole }) {
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post(`${BACKEND}/auth/login`, { username: user, password: pass });
      setToken(res.data.access_token);
      setRole(res.data.role);
    } catch (err) {
      setError('Invalid credentials');
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0f18] flex items-center justify-center p-4">
      <div className="bg-[#121824] p-8 rounded-lg shadow-xl w-full max-w-md border border-gray-800">
        <div className="flex items-center justify-center mb-8">
          <Shield className="w-12 h-12 text-blue-500 mr-3" />
          <h1 className="text-2xl font-bold text-gray-100">Enterprise Honeypot</h1>
        </div>
        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="text-gray-400 text-sm">Username</label>
            <input type="text" className="w-full bg-[#0a0f18] border border-gray-700 rounded p-2 text-white mt-1 focus:border-blue-500 outline-none" value={user} onChange={(e) => setUser(e.target.value)} required />
          </div>
          <div>
            <label className="text-gray-400 text-sm">Password</label>
            <input type="password" className="w-full bg-[#0a0f18] border border-gray-700 rounded p-2 text-white mt-1 focus:border-blue-500 outline-none" value={pass} onChange={(e) => setPass(e.target.value)} required />
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition-colors">
            Login
          </button>
        </form>
        <div className="mt-6 text-xs text-gray-500 text-center">
          Available Roles: Admin (admin123), Analyst (analyst123), Viewer (viewer123)
        </div>
      </div>
    </div>
  );
}
