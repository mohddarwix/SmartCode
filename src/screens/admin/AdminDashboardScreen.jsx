import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Users, Layers, BookOpen, Send, Activity, AlertCircle } from 'lucide-react';
import { adminApi } from '../../api/admin';

export default function AdminDashboardScreen() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    adminApi
      .stats()
      .then((s) => !cancelled && setStats(s))
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <Spinner />;

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-1">Admin overview</h1>
      <p className="text-gray-600 text-sm mb-6">Monitor system activity, content, and users.</p>

      {error && (
        <div className="mb-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3 flex items-center">
          <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Users"       value={stats?.users}       icon={Users}    color="bg-indigo-100 text-indigo-700" to="/admin/users" />
        <StatCard label="Problems"    value={stats?.problems}    icon={BookOpen} color="bg-green-100 text-green-700"   to="/admin/problems" />
        <StatCard label="Skills"      value={stats?.skills}      icon={Layers}   color="bg-yellow-100 text-yellow-700" to="/admin/skills" />
        <StatCard label="Submissions" value={stats?.submissions} icon={Send}     color="bg-purple-100 text-purple-700" to="/admin/users" />
      </div>

      <div className="bg-white rounded-xl shadow-md p-6">
        <div className="flex items-center mb-4">
          <Activity className="w-5 h-5 text-indigo-600 mr-2" />
          <h2 className="text-lg font-bold text-gray-800">Submissions this week</h2>
        </div>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={stats?.submissions_last_7_days || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="count" fill="#4f46e5" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function StatCard({ label, value, icon: Icon, color, to }) {
  return (
    <Link to={to} className="bg-white rounded-xl shadow-md p-5 hover:shadow-lg transition">
      <div className={`inline-flex items-center justify-center w-10 h-10 rounded-lg ${color} mb-3`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="text-3xl font-bold text-gray-800">{value ?? '-'}</div>
      <div className="text-sm text-gray-600">{label}</div>
    </Link>
  );
}

function Spinner() {
  return (
    <div className="min-h-[300px] flex items-center justify-center">
      <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
    </div>
  );
}
