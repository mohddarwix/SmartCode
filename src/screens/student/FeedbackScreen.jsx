import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { CheckCircle, XCircle, AlertCircle, ChevronRight, RotateCcw } from 'lucide-react';
import { submissionsApi } from '../../api/submissions';
import { CaseResultsList } from './EditorScreen';

const colorFor = (value) =>
  value >= 80 ? 'bg-green-600' : value >= 60 ? 'bg-yellow-500' : 'bg-red-500';

const statusBadge = (status) =>
  status === 'accepted' ? 'text-green-700 bg-green-100' :
  status === 'pending'  ? 'text-gray-700 bg-gray-100'   :
                          'text-red-700 bg-red-100';

export default function FeedbackScreen() {
  const navigate = useNavigate();
  const { submissionId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    submissionsApi
      .get(submissionId)
      .then((res) => !cancelled && setData(res))
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [submissionId]);

  if (loading) {
    return (
      <div className="min-h-[300px] flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-2xl mx-auto p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 flex items-center">
          <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
          {error || 'Submission not found.'}
        </div>
        <Link to="/problems" className="text-sm text-indigo-600 mt-4 inline-block">&larr; Back to problems</Link>
      </div>
    );
  }

  const accepted = data.status === 'accepted';
  const breakdown = data.metrics
    ? [
        { label: 'Correctness',     value: data.metrics.score_correctness },
        { label: 'Edge Cases',      value: data.metrics.score_edge_cases },
        { label: 'Code Quality',    value: data.metrics.score_code_quality },
        { label: 'Time Complexity', value: data.metrics.score_time_complexity },
      ]
    : [];

  const failingCases = (data.cases || []).filter((c) => !c.passed);

  return (
    <div className="max-w-4xl mx-auto p-8 space-y-6">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-6">
          <div
            className={`inline-flex items-center justify-center w-20 h-20 rounded-full mb-4 ${
              accepted ? 'bg-green-100' : 'bg-red-100'
            }`}
          >
            {accepted ? (
              <CheckCircle className="w-12 h-12 text-green-600" />
            ) : (
              <XCircle className="w-12 h-12 text-red-600" />
            )}
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            {accepted ? 'Accepted!' : 'Not accepted yet'}
          </h1>
          <div className="flex items-center justify-center gap-3 text-lg text-gray-600 flex-wrap">
            <span className={`px-3 py-0.5 text-sm font-semibold rounded ${statusBadge(data.status)}`}>
              {data.status.replace('_', ' ')}
            </span>
            <span>
              Score: <span className="font-bold text-indigo-600">{data.score}/100</span>
            </span>
            {data.metrics && (
              <span className="text-sm">
                ({data.metrics.passed_count}/{data.metrics.total_count} tests)
              </span>
            )}
            {data.total_runtime_ms != null && (
              <span className="text-xs text-gray-600 bg-gray-100 px-2 py-0.5 rounded">
                Runtime: {data.total_runtime_ms} ms
              </span>
            )}
            {data.total_memory_kb != null && data.total_memory_kb > 0 && (
              <span className="text-xs text-gray-600 bg-gray-100 px-2 py-0.5 rounded">
                Memory: {data.total_memory_kb < 1024
                  ? `${data.total_memory_kb} KB`
                  : `${(data.total_memory_kb / 1024).toFixed(1)} MB`}
              </span>
            )}
            {data.grader_source === 'heuristic' && (
              <span className="text-[10px] uppercase tracking-wide text-gray-500">heuristic only</span>
            )}
          </div>
          {data.score_adjustment && data.score_adjustment.raw_score > data.score_adjustment.final_score && (
            <p className="text-sm text-amber-700 mt-2">
              Adjusted from <span className="font-semibold">{data.score_adjustment.raw_score}</span>
              {' '}&rarr;{' '}
              <span className="font-semibold">{data.score_adjustment.final_score}</span>
              {' '}({data.score_adjustment.prior_failed_attempts} previous failed{' '}
              {data.score_adjustment.prior_failed_attempts === 1 ? 'attempt' : 'attempts'},{' '}
              -{data.score_adjustment.raw_score - data.score_adjustment.final_score} points)
            </p>
          )}
          <p className="text-sm text-gray-500 mt-2">
            Problem:{' '}
            <Link to={`/problems/${data.problem_id}`} className="text-indigo-600 hover:underline">
              {data.problem_title}
            </Link>
          </p>
        </div>

        {!accepted && failingCases.length > 0 && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded-r">
            <p className="text-red-900 font-medium flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {failingCases.length} test case{failingCases.length === 1 ? '' : 's'} failed. Fix them and resubmit — you can't move on to the next problem until all tests pass.
            </p>
          </div>
        )}

        {data.feedback_summary_md && (
          <div className="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6 rounded-r">
            <p className="text-blue-900 font-medium mb-2">{data.feedback_summary_md}</p>
            {data.feedback_bullets?.length > 0 && (
              <ul className="text-blue-800 space-y-1 text-sm">
                {data.feedback_bullets.map((b, i) => (
                  <li key={i}>
                    {b.kind === 'good' ? '+' : '!'} {b.text}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {breakdown.length > 0 && (
          <div className="bg-gray-50 rounded-lg p-6 mb-6">
            <h3 className="font-bold text-gray-800 mb-4">Performance Breakdown</h3>
            <div className="space-y-3">
              {breakdown.map((row) => (
                <div key={row.label} className="flex items-center justify-between">
                  <span className="text-gray-700">{row.label}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className={`${colorFor(row.value)} h-2 rounded-full`}
                        style={{ width: `${row.value}%` }}
                      />
                    </div>
                    <span className="text-sm font-bold text-gray-700 w-10 text-right">{row.value}%</span>
                  </div>
                </div>
              ))}
              {data.metrics?.inferred_big_o && (
                <div className="text-xs text-gray-500 pt-2">
                  Inferred complexity:{' '}
                  <code className="bg-white border border-gray-200 rounded px-1.5 py-0.5">
                    {data.metrics.inferred_big_o}
                  </code>
                </div>
              )}
            </div>
          </div>
        )}

        {data.cases && data.cases.length > 0 && (
          <div className="mb-6">
            <h3 className="font-bold text-gray-800 mb-3">Test case results</h3>
            <CaseResultsList
              result={{
                cases: data.cases,
                passed_count: data.metrics?.passed_count ?? data.cases.filter((c) => c.passed).length,
                total_count: data.metrics?.total_count ?? data.cases.length,
                all_passed: accepted,
                source: data.grader_source || 'llm',
              }}
            />
          </div>
        )}

        {accepted && data.skills_updated?.length > 0 && (
          <div className="bg-green-50 border-l-4 border-green-600 p-4 mb-6 rounded-r">
            <h3 className="font-semibold text-green-900 mb-2">Skills Updated</h3>
            <div className="text-green-800 text-sm space-y-1">
              {data.skills_updated.map((s) => {
                const delta = s.after - s.before;
                const sign = delta > 0 ? '+' : '';
                return (
                  <p key={s.skill}>
                    - {s.skill}: {s.before}% &rarr; {s.after}% ({sign}
                    {delta}%)
                  </p>
                );
              })}
            </div>
          </div>
        )}

        {accepted && (data.next_problems?.length > 0 || data.next_problem) && (
          <div className="mb-6">
            <h3 className="font-semibold text-purple-900 mb-3">
              Recommended next problems
              <span className="ml-2 text-xs font-normal text-purple-700">choose any</span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {(data.next_problems?.length ? data.next_problems : [data.next_problem]).filter(Boolean).map((rec, idx) => {
                const isPrimary = idx === 0;
                const cardCls = isPrimary
                  ? 'bg-gradient-to-br from-purple-600 to-indigo-600 text-white'
                  : 'bg-white border border-purple-200 text-gray-800';
                const reasonCls = isPrimary ? 'text-white/90' : 'text-gray-600';
                const btnCls = isPrimary
                  ? 'bg-white text-purple-700 hover:bg-gray-100'
                  : 'bg-purple-600 text-white hover:bg-purple-700';
                return (
                  <div key={rec.problem_id} className={`${cardCls} rounded-lg shadow-sm p-4 flex flex-col`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-semibold uppercase ${isPrimary ? 'opacity-90' : 'text-purple-600'}`}>
                        {isPrimary ? 'Top pick' : `Option ${idx + 1}`}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full uppercase ${isPrimary ? 'bg-white/20' : 'bg-purple-100 text-purple-700'}`}>
                        {rec.difficulty}
                      </span>
                    </div>
                    <h4 className="text-base font-bold mb-1">{rec.title}</h4>
                    {rec.reason_md && (
                      <p className={`text-xs mb-3 flex-1 ${reasonCls}`}>{rec.reason_md}</p>
                    )}
                    <button
                      onClick={() => navigate(`/problems/${rec.problem_id}`)}
                      className={`px-3 py-1.5 rounded font-semibold text-sm transition flex items-center justify-center gap-1 ${btnCls}`}
                    >
                      Start
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="flex flex-wrap gap-3">
          {accepted ? (
            <>
              <button
                onClick={() => navigate('/dashboard')}
                className="flex-1 bg-gray-200 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-300 transition"
              >
                Back to Dashboard
              </button>
              {(() => {
                const topPick = (data.next_problems && data.next_problems[0]) || data.next_problem;
                return (
                  <button
                    onClick={() => navigate(topPick ? `/problems/${topPick.problem_id}` : '/problems')}
                    className="flex-1 bg-indigo-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-indigo-700 transition flex items-center justify-center gap-1"
                  >
                    {topPick ? 'Try Top Pick' : 'Browse Problems'}
                    <ChevronRight className="w-4 h-4" />
                  </button>
                );
              })()}
            </>
          ) : (
            <>
              <button
                onClick={() => navigate('/problems')}
                className="flex-1 bg-gray-200 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-300 transition"
              >
                Problem List
              </button>
              <button
                onClick={() => navigate(`/problems/${data.problem_id}`)}
                className="flex-1 bg-red-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-red-700 transition flex items-center justify-center gap-2"
              >
                <RotateCcw className="w-4 h-4" />
                Fix &amp; Resubmit
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
