import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts';
import { TrendingUp, ChevronRight, AlertCircle } from 'lucide-react';
import { skillsApi } from '../../api/skills';

export default function DashboardScreen() {
  const [skills, setSkills] = useState([]);
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    skillsApi
      .mySkills()
      .then((data) => {
        if (cancelled) return;
        setSkills(data);
        if (data.length) setSelectedSkill(data[0]);
      })
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedSkill) return;
    let cancelled = false;
    skillsApi
      .mySkillHistory(selectedSkill.skill_id)
      .then((data) => !cancelled && setHistory(data))
      .catch(() => !cancelled && setHistory([]));
    return () => {
      cancelled = true;
    };
  }, [selectedSkill?.skill_id]);

  if (loading) return <FullPageSpinner />;

  const radarData = skills.map((s) => ({ skill: s.name, score: s.score, fullMark: 100 }));
  const historyData = history.map((h) => ({ week: formatDay(h.day), score: h.score }));

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 flex items-center">
            <TrendingUp className="w-6 h-6 mr-2 text-indigo-600" />
            Skills &amp; Progress
          </h1>
          <p className="text-gray-600 text-sm">An overview of your skill profile and recent progress.</p>
        </div>
        <Link
          to="/problems"
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition flex items-center"
        >
          Browse problems
          <ChevronRight className="w-4 h-4 ml-1" />
        </Link>
      </div>

      {error && (
        <div className="mb-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3 flex items-center">
          <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-md p-4">
            <h2 className="text-lg font-bold text-gray-800 mb-3">Your Skills</h2>
            <div className="space-y-2">
              {skills.map((skill) => (
                <button
                  key={skill.skill_id}
                  onClick={() => setSelectedSkill(skill)}
                  className={`w-full text-left p-2 rounded-lg transition ${
                    selectedSkill?.skill_id === skill.skill_id
                      ? 'bg-indigo-50 border-2 border-indigo-300'
                      : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-gray-700 text-sm">{skill.name}</span>
                    <span className="text-xs font-bold text-indigo-600">{skill.score}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-indigo-600 h-1.5 rounded-full transition-all"
                      style={{ width: `${skill.score}%` }}
                    />
                  </div>
                </button>
              ))}
              {skills.length === 0 && (
                <p className="text-sm text-gray-500 py-2">No skill data yet. Solve a problem to start tracking your progress.</p>
              )}
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">Skills Overview</h2>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="skill" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                <Radar name="Your Skills" dataKey="score" stroke="#4f46e5" fill="#4f46e5" fillOpacity={0.6} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {selectedSkill && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">Progress: {selectedSkill.name}</h2>
              {historyData.length > 1 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={historyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="week" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Line type="monotone" dataKey="score" stroke="#4f46e5" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-sm text-gray-500 py-6 text-center">
                  Not enough history yet. Submit a few solutions and the trend will start here.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function formatDay(iso) {
  // "2026-04-13" -> "Apr 13"
  const d = new Date(`${iso}T00:00:00`);
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric' });
}

function FullPageSpinner() {
  return (
    <div className="min-h-[300px] flex items-center justify-center">
      <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
    </div>
  );
}
