import { useEffect, useState } from 'react';
import { Search, AlertCircle, Shield, X, Eye } from 'lucide-react';
import { adminApi } from '../../api/admin';

export default function AdminUsersScreen() {
  const [users, setUsers] = useState([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [drilldown, setDrilldown] = useState(null); // user_id being inspected

  useEffect(() => {
    let cancelled = false;
    adminApi
      .users()
      .then((u) => !cancelled && setUsers(u))
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = users.filter(
    (u) =>
      u.full_name.toLowerCase().includes(query.toLowerCase()) ||
      u.email.toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Users</h1>
        <p className="text-gray-600 text-sm">Monitor learner activity and performance.</p>
      </div>

      {error && (
        <div className="mb-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3 flex items-center">
          <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
          {error}
        </div>
      )}

      <div className="bg-white rounded-xl shadow-md p-4 mb-4">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name or email..."
            className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-md overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
            <tr>
              <th className="text-left px-4 py-3">Name</th>
              <th className="text-left px-4 py-3 hidden sm:table-cell">Email</th>
              <th className="text-left px-4 py-3">Role</th>
              <th className="text-left px-4 py-3">Solved</th>
              <th className="text-left px-4 py-3">Avg score</th>
              <th className="text-left px-4 py-3 hidden lg:table-cell">Last active</th>
              <th className="text-right px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={7} className="text-center text-gray-500 py-8">Loading...</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={7} className="text-center text-gray-500 py-8">No users match your search.</td></tr>
            ) : (
              filtered.map((u) => (
                <tr key={u.user_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-800">{u.full_name}</td>
                  <td className="px-4 py-3 hidden sm:table-cell text-gray-700">{u.email}</td>
                  <td className="px-4 py-3">
                    {u.role === 'admin' ? (
                      <span className="inline-flex items-center text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded text-xs">
                        <Shield className="w-3 h-3 mr-1" /> admin
                      </span>
                    ) : (
                      <span className="text-gray-700 text-xs">student</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-700">{u.solved}</td>
                  <td className="px-4 py-3 font-medium text-gray-800">{u.avg_score}%</td>
                  <td className="px-4 py-3 hidden lg:table-cell text-gray-600">
                    {u.last_login_at ? new Date(u.last_login_at).toLocaleString() : '-'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setDrilldown(u.user_id)}
                      className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-800 text-xs font-medium"
                    >
                      <Eye className="w-3.5 h-3.5" /> View
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {drilldown && (
        <UserDrilldown userId={drilldown} onClose={() => setDrilldown(null)} />
      )}
    </div>
  );
}

// ===========================================================================
// Per-user drilldown modal (FR-Admin 5)
// ===========================================================================
function UserDrilldown({ userId, onClose }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    adminApi.userDetail(userId)
      .then((d) => !cancelled && setData(d))
      .catch((err) => !cancelled && setError(err.message));
    return () => { cancelled = true; };
  }, [userId]);

  const eventColor = (t) =>
    t.startsWith('submission.accepted') ? 'bg-green-100 text-green-800' :
    t.startsWith('submission.')         ? 'bg-red-100 text-red-800' :
    t.startsWith('login.success')       ? 'bg-blue-100 text-blue-800' :
    t.startsWith('login.failed')        ? 'bg-yellow-100 text-yellow-800' :
    t.startsWith('register.')           ? 'bg-indigo-100 text-indigo-800' :
                                          'bg-gray-100 text-gray-700';

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-bold text-gray-800">
            {data ? data.user.full_name : 'Loading...'}
          </h2>
          <button onClick={onClose} className="p-2 rounded hover:bg-gray-100" title="Close">
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {error && (
          <div className="mx-6 mt-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-2 flex items-center">
            <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
            {error}
          </div>
        )}

        {data && (
          <div className="flex-1 overflow-y-auto p-6 space-y-5">
            {/* Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <Stat label="Email"          value={data.user.email} />
              <Stat label="Role"           value={data.user.role} />
              <Stat label="Solved"         value={data.user.solved} />
              <Stat label="Average score"  value={`${data.user.avg_score}%`} />
            </div>

            {/* Skill bars */}
            <div>
              <h3 className="text-sm font-semibold text-gray-800 mb-2">Skill scores</h3>
              <div className="space-y-2">
                {data.skill_scores.map((s) => (
                  <div key={s.skill_id} className="text-xs">
                    <div className="flex justify-between mb-1">
                      <span className="text-gray-700">{s.name}</span>
                      <span className="font-medium text-gray-800">{s.score}%</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5">
                      <div className="bg-indigo-600 h-1.5 rounded-full" style={{ width: `${s.score}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent submissions */}
            <div>
              <h3 className="text-sm font-semibold text-gray-800 mb-2">
                Recent submissions ({data.recent_submissions.length})
              </h3>
              {data.recent_submissions.length === 0 ? (
                <p className="text-xs text-gray-500">No submissions yet.</p>
              ) : (
                <div className="space-y-1 text-xs">
                  {data.recent_submissions.map((s) => (
                    <div key={s.submission_id} className="flex items-center gap-3 border border-gray-100 rounded p-2">
                      <span className={`px-2 py-0.5 rounded font-semibold ${eventColor(`submission.${s.status}`)}`}>
                        {s.status.replace('_', ' ')}
                      </span>
                      <span className="font-medium text-gray-700">{s.score}/100</span>
                      <span className="text-gray-500 text-[10px]">
                        {new Date(s.submitted_at).toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Audit timeline */}
            <div>
              <h3 className="text-sm font-semibold text-gray-800 mb-2">
                Audit timeline (newest {data.audit_events.length})
              </h3>
              {data.audit_events.length === 0 ? (
                <p className="text-xs text-gray-500">No audit events yet.</p>
              ) : (
                <ul className="space-y-1 text-xs">
                  {data.audit_events.map((e, i) => (
                    <li key={i} className="flex items-start gap-2 border-l-2 border-gray-200 pl-2 py-1">
                      <span className={`text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded ${eventColor(e.event_type)}`}>
                        {e.event_type}
                      </span>
                      <span className="text-gray-700 flex-1">{e.detail || '-'}</span>
                      <span className="text-gray-400 text-[10px] whitespace-nowrap">
                        {new Date(e.when).toLocaleString()}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded p-3">
      <div className="text-[10px] uppercase text-gray-500 font-semibold">{label}</div>
      <div className="text-sm font-medium text-gray-800 mt-1 break-all">{value}</div>
    </div>
  );
}
