import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Code, Play, ChevronRight, BookOpen, CheckCircle2, Circle, CircleDashed, AlertCircle } from 'lucide-react';
import { problemsApi } from '../../api/problems';
import { recommendationsApi } from '../../api/recommendations';

const difficultyClass = (d) =>
  d === 'easy'   ? 'text-green-700 bg-green-100'  :
  d === 'medium' ? 'text-yellow-700 bg-yellow-100' :
                   'text-red-700 bg-red-100';

const statusIcon = (s) => {
  if (s === 'solved')    return <CheckCircle2 className="w-4 h-4 text-green-600" />;
  if (s === 'attempted') return <CircleDashed className="w-4 h-4 text-yellow-600" />;
  return <Circle className="w-4 h-4 text-gray-300" />;
};

export default function ProblemListScreen() {
  const navigate = useNavigate();
  const [problems, setProblems] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all'); // all | solved | unsolved
  const [search, setSearch] = useState('');

  useEffect(() => {
    let cancelled = false;
    Promise.all([problemsApi.list(), recommendationsApi.next().catch(() => [])])
      .then(([list, recs]) => {
        if (cancelled) return;
        setProblems(list);
        // Endpoint now returns an array of up to 3 picks (was single object before)
        setRecommendations(Array.isArray(recs) ? recs : (recs ? [recs] : []));
      })
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <FullPageSpinner />;

  const filtered = problems
    .filter((p) => (filter === 'solved' ? p.user_status === 'solved' : filter === 'unsolved' ? p.user_status !== 'solved' : true))
    .filter((p) => p.title.toLowerCase().includes(search.toLowerCase()) || p.skills.join(',').toLowerCase().includes(search.toLowerCase()));

  const solvedCount = problems.filter((p) => p.user_status === 'solved').length;

  return (
    <div className="max-w-7xl mx-auto p-6">
      {recommendations.length > 0 && (
        <div className="mb-6">
          <div className="flex items-baseline justify-between mb-3">
            <h3 className="text-lg font-bold text-gray-800">Recommended for you</h3>
            <span className="text-xs text-gray-500">{recommendations.length} pick{recommendations.length === 1 ? '' : 's'} - choose any</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {recommendations.map((rec, idx) => {
              const isPrimary = idx === 0;
              const accent = isPrimary
                ? 'bg-gradient-to-br from-indigo-600 to-purple-600 text-white'
                : 'bg-white border border-indigo-200 text-gray-800';
              const reasonClass = isPrimary ? 'text-white/90' : 'text-gray-600';
              const buttonClass = isPrimary
                ? 'bg-white text-indigo-600 hover:bg-gray-100'
                : 'bg-indigo-600 text-white hover:bg-indigo-700';
              return (
                <div key={rec.problem_id} className={`${accent} rounded-xl shadow-md p-5 flex flex-col`}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`text-xs font-semibold uppercase tracking-wide ${isPrimary ? 'opacity-90' : 'text-indigo-600'}`}>
                      {isPrimary ? 'Top pick' : `Option ${idx + 1}`}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${isPrimary ? 'bg-white/20' : difficultyClass(rec.difficulty)}`}>
                      {capitalize(rec.difficulty)}
                    </span>
                  </div>
                  <h4 className="text-lg font-bold mb-1">{rec.title}</h4>
                  {rec.reason_md && (
                    <p className={`text-xs mb-4 flex-1 ${reasonClass}`}>{rec.reason_md}</p>
                  )}
                  <Link
                    to={`/problems/${rec.problem_id}`}
                    className={`px-4 py-2 rounded-lg font-semibold text-sm transition flex items-center justify-center gap-1 ${buttonClass}`}
                  >
                    Start
                    <ChevronRight className="w-4 h-4" />
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-md p-6">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
          <h2 className="text-xl font-bold text-gray-800 flex items-center">
            <BookOpen className="w-5 h-5 mr-2 text-indigo-600" />
            Your Journey
            <span className="ml-3 text-sm font-normal text-gray-500">
              {solvedCount} / {problems.length} solved
            </span>
          </h2>

          <div className="flex items-center gap-2 flex-wrap">
            <FilterPill active={filter === 'all'} onClick={() => setFilter('all')}>All</FilterPill>
            <FilterPill active={filter === 'unsolved'} onClick={() => setFilter('unsolved')}>To Do</FilterPill>
            <FilterPill active={filter === 'solved'} onClick={() => setFilter('solved')}>Solved</FilterPill>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search..."
              className="ml-2 px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
        </div>

        {error && (
          <div className="mb-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3 flex items-center">
            <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
            {error}
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-gray-600 uppercase text-xs border-b">
              <tr>
                <th className="text-left px-3 py-2 w-8"></th>
                <th className="text-left px-3 py-2">Title</th>
                <th className="text-left px-3 py-2 hidden sm:table-cell">Difficulty</th>
                <th className="text-left px-3 py-2 hidden lg:table-cell">Skills</th>
                <th className="text-left px-3 py-2 hidden md:table-cell">Best</th>
                <th className="text-right px-3 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((p) => (
                <tr key={p.problem_id} className="hover:bg-gray-50">
                  <td className="px-3 py-3" title={p.user_status}>{statusIcon(p.user_status)}</td>
                  <td className="px-3 py-3 font-medium text-gray-800">
                    <button
                      onClick={() => navigate(`/problems/${p.problem_id}`)}
                      className="hover:text-indigo-700"
                    >
                      {p.problem_id}. {p.title}
                    </button>
                  </td>
                  <td className="px-3 py-3 hidden sm:table-cell">
                    <span className={`px-2 py-0.5 rounded text-xs ${difficultyClass(p.difficulty)}`}>
                      {capitalize(p.difficulty)}
                    </span>
                  </td>
                  <td className="px-3 py-3 hidden lg:table-cell text-gray-600">{p.skills.join(', ')}</td>
                  <td className="px-3 py-3 hidden md:table-cell text-gray-700">
                    {p.best_score > 0 ? `${p.best_score}%` : '-'}
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex justify-end gap-1">
                      <button
                        onClick={() => navigate(`/problems/${p.problem_id}`)}
                        className="bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded font-medium hover:bg-indigo-100 transition flex items-center text-xs"
                      >
                        <Code className="w-3 h-3 mr-1" />
                        Solve
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center text-gray-500 py-8">
                    {problems.length === 0
                      ? 'No problems unlocked yet. Complete the diagnostic to get your first recommendation — the AI will unlock new problems as you progress.'
                      : 'No problems match your filter.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function FilterPill({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-full text-xs font-medium transition ${
        active ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      }`}
    >
      {children}
    </button>
  );
}

function capitalize(s) {
  return s ? s[0].toUpperCase() + s.slice(1) : s;
}

function FullPageSpinner() {
  return (
    <div className="min-h-[300px] flex items-center justify-center">
      <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
    </div>
  );
}
