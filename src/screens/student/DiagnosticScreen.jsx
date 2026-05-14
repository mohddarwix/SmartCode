import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  BookOpen,
  Play,
  Send,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Sparkles,
  ChevronRight,
} from 'lucide-react';
import { diagnosticQuestions } from '../../data/mock';
import { diagnosticApi } from '../../api/diagnostic';
import { useAuth } from '../../context/AuthContext';

// Three phases: intro -> answering -> review.
const PHASE = { INTRO: 'intro', ANSWERING: 'answering', REVIEW: 'review' };

export default function DiagnosticScreen() {
  const { setUser } = useAuth();
  const navigate = useNavigate();

  const [phase, setPhase] = useState(PHASE.INTRO);
  const [startTime, setStartTime] = useState(null);
  const [answers, setAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  // Coding-only diagnostic. Each question targets a different skill; the spec
  // is deliberately terse so a careless student misses the edge case that's
  // hidden in the grader's test inputs.
  const codings = useMemo(() => diagnosticQuestions, []);

  const handleCode = (id, code) => setAnswers((p) => ({ ...p, [id]: code }));

  // Pre-fill answers with each question's placeholder so the editor isn't empty.
  useEffect(() => {
    setAnswers((prev) => {
      const next = { ...prev };
      for (const q of codings) {
        if (next[q.id] == null) next[q.id] = q.placeholder || '';
      }
      return next;
    });
  }, [codings]);

  const handleStart = () => {
    setPhase(PHASE.ANSWERING);
    setStartTime(Date.now());
  };

  const handleSubmit = async () => {
    setError('');
    setSubmitting(true);
    try {
      const totalSec = Math.max(1, Math.round((Date.now() - (startTime || Date.now())) / 1000));
      const perItem = Math.max(1, Math.round(totalSec / codings.length));

      const items = codings.map((q, idx) => ({
        order_index: idx + 1,
        skill_name: q.skill,
        tested_skills: q.testedSkills || [q.skill],
        type: 'coding',
        question: q.question,
        user_answer: (answers[q.id] || '').trim(),
        correct_answer: null,
        time_spent_seconds: perItem,
        hints_used: 0,
      }));

      const data = await diagnosticApi.submit(items);
      setUser(data.user);
      setResult(data);
      setPhase(PHASE.REVIEW);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setError(err.message || 'Could not save the diagnostic.');
    } finally {
      setSubmitting(false);
    }
  };

  // ---------------------------------- INTRO ---------------------------------
  if (phase === PHASE.INTRO) {
    return (
      <div className="max-w-4xl mx-auto p-8">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-indigo-100 rounded-full mb-4">
              <BookOpen className="w-10 h-10 text-indigo-600" />
            </div>
            <h1 className="text-3xl font-bold text-gray-800 mb-3">Diagnostic Assessment</h1>
            <p className="text-gray-600 max-w-2xl mx-auto">
              SmartCode's AI grades your answers, identifies your strongest and weakest skills,
              explains every mistake, and picks the right problem for you to start with.
            </p>
          </div>

          <div className="bg-indigo-50 border-l-4 border-indigo-600 p-4 mb-6 rounded-r">
            <h3 className="font-semibold text-indigo-900 mb-2">What to expect:</h3>
            <ul className="text-indigo-800 space-y-1 text-sm">
              <li>- {codings.length} short coding problems, one per core skill</li>
              <li>- Each problem looks simple, but watch out — the AI grader checks edge cases the spec doesn't mention</li>
              <li>- An AI-written breakdown of where you got things right and wrong</li>
              <li>- A recommended first problem tailored to your weakest skills</li>
              <li>- Estimated time: 20-30 minutes</li>
            </ul>
          </div>

          <button
            onClick={handleStart}
            className="w-full bg-indigo-600 text-white py-4 rounded-lg font-semibold text-lg hover:bg-indigo-700 transition flex items-center justify-center space-x-2"
          >
            <Play className="w-6 h-6" />
            <span>Start Diagnostic Exam</span>
          </button>
        </div>
      </div>
    );
  }

  // ---------------------------------- REVIEW --------------------------------
  if (phase === PHASE.REVIEW && result) {
    const firstPick = (result.next_problems && result.next_problems[0]) || result.next_problem;
    return <DiagnosticReview result={result} onContinue={() => navigate(firstPick ? `/problems/${firstPick.problem_id}` : '/dashboard')} />;
  }

  // -------------------------------- ANSWERING -------------------------------
  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-2">Diagnostic Test</h1>
      <p className="text-sm text-gray-500 mb-8">
        Complete each function. The AI grader runs your code against several inputs, including
        edge cases the prompt doesn't enumerate — so think about empty / tiny / duplicate inputs.
      </p>

      {codings.map((q, idx) => (
        <div key={q.id} className="bg-white rounded-xl shadow-md p-6 mb-6">
          <div className="flex items-start justify-between mb-4 gap-3">
            <div>
              <h3 className="text-lg font-bold text-gray-800 mb-2">
                {idx + 1}. {q.question}
              </h3>
              {q.expected && (
                <p className="text-sm text-gray-600 font-mono">{q.expected}</p>
              )}
            </div>
            <div className="flex gap-2 flex-wrap justify-end max-w-xs">
              {(q.testedSkills || [q.skill]).map((s) => (
                <span
                  key={s}
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    s === q.skill ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {s}
                </span>
              ))}
              <span className="bg-yellow-100 text-yellow-700 px-3 py-1 rounded-full text-xs font-medium">{q.difficulty}</span>
            </div>
          </div>

          <textarea
            value={answers[q.id] ?? q.placeholder ?? ''}
            onChange={(e) => handleCode(q.id, e.target.value)}
            spellCheck={false}
            className="w-full h-48 p-4 bg-gray-900 text-green-400 font-mono text-sm rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          />
        </div>
      ))}

      {error && (
        <div className="mb-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3 flex items-center">
          <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
          {error}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={submitting}
        className="w-full bg-indigo-600 text-white py-4 rounded-lg font-semibold text-lg hover:bg-indigo-700 transition flex items-center justify-center space-x-2 disabled:opacity-60"
      >
        <Send className="w-6 h-6" />
        <span>{submitting ? 'AI is grading your answers...' : 'Complete Diagnostic'}</span>
      </button>
    </div>
  );
}

// ============================================================================
// Review screen — shown after the LLM grades the diagnostic
// ============================================================================
function DiagnosticReview({ result, onContinue }) {
  const correctCount = result.items.filter((it) => it.is_correct).length;
  const total = result.items.length;
  const weakSet = new Set(result.weak_skills || []);

  return (
    <div className="max-w-4xl mx-auto p-8 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-lg p-8 text-center">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-indigo-100 rounded-full mb-4">
          <Sparkles className="w-10 h-10 text-indigo-600" />
        </div>
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Your AI-graded results</h1>
        <p className="text-gray-600">
          {correctCount} of {total} correct &middot; Overall score:{' '}
          <span className="font-bold text-indigo-600">{result.overall_score}/100</span>
        </p>
        {result.grader_source === 'heuristic' && (
          <p className="text-xs text-gray-500 mt-3">
            AI grading was unavailable; these results came from a rule-based scorer. The corrections will be more detailed once the LLM is reachable.
          </p>
        )}
      </div>

      {/* Summary */}
      {result.summary_md && (
        <div className="bg-indigo-50 border-l-4 border-indigo-600 p-5 rounded-r">
          <h2 className="font-semibold text-indigo-900 mb-1">Summary</h2>
          <p className="text-indigo-900/90 text-sm whitespace-pre-line">{result.summary_md}</p>
        </div>
      )}

      {/* Skill scores */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="font-bold text-gray-800 mb-4">Your skill profile</h2>
        <div className="space-y-3">
          {result.skill_scores.map((s) => {
            const isWeak = weakSet.has(s.name);
            return (
              <div key={s.skill_id}>
                <div className="flex items-center justify-between mb-1 text-sm">
                  <span className={`font-medium ${isWeak ? 'text-red-700' : 'text-gray-800'}`}>
                    {s.name}
                    {isWeak && <span className="ml-2 text-xs uppercase tracking-wide">focus area</span>}
                  </span>
                  <span className="font-bold text-gray-700">{s.score}%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${isWeak ? 'bg-red-500' : 'bg-indigo-600'}`}
                    style={{ width: `${s.score}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Per-item corrections */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="font-bold text-gray-800 mb-4">Question-by-question review</h2>
        <div className="space-y-4">
          {result.items.map((it) => (
            <ReviewItem key={it.order_index} item={it} />
          ))}
        </div>
      </div>

      {/* Next problems (up to 3 picks) */}
      {(result.next_problems && result.next_problems.length > 0) ? (
        <div>
          <div className="flex items-baseline justify-between mb-3">
            <h3 className="text-lg font-bold text-gray-800">Recommended next problems</h3>
            <span className="text-xs text-gray-500">{result.next_problems.length} pick{result.next_problems.length === 1 ? '' : 's'} - choose any</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {result.next_problems.map((rec, idx) => {
              const isPrimary = idx === 0;
              const accent = isPrimary
                ? 'bg-gradient-to-br from-indigo-600 to-purple-600 text-white'
                : 'bg-white border border-indigo-200 text-gray-800';
              const reasonClass = isPrimary ? 'text-white/90' : 'text-gray-600';
              const diffPillClass = isPrimary
                ? 'bg-white/20'
                : rec.difficulty === 'easy' ? 'text-green-700 bg-green-100'
                : rec.difficulty === 'medium' ? 'text-yellow-700 bg-yellow-100'
                : 'text-red-700 bg-red-100';
              const buttonClass = isPrimary
                ? 'bg-white text-indigo-700 hover:bg-gray-100'
                : 'bg-indigo-600 text-white hover:bg-indigo-700';
              return (
                <div key={rec.problem_id} className={`${accent} rounded-xl shadow-md p-5 flex flex-col`}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`text-xs font-semibold uppercase tracking-wide ${isPrimary ? 'opacity-90' : 'text-indigo-600'}`}>
                      {isPrimary ? 'Top pick' : `Option ${idx + 1}`}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full uppercase ${diffPillClass}`}>
                      {rec.difficulty}
                    </span>
                    {rec.estimated_minutes && (
                      <span className={`text-xs ${isPrimary ? 'opacity-75' : 'text-gray-500'}`}>~{rec.estimated_minutes} min</span>
                    )}
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
      ) : (
        <div className="text-center">
          <button
            onClick={onContinue}
            className="bg-indigo-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-indigo-700 transition"
          >
            Continue to dashboard
          </button>
        </div>
      )}

      <p className="text-center">
        <Link to="/dashboard" className="text-sm text-gray-500 hover:text-gray-700">
          Skip and go to dashboard
        </Link>
      </p>
    </div>
  );
}

function ReviewItem({ item }) {
  const correct = item.is_correct === true;
  const wrong = item.is_correct === false;

  return (
    <div
      className={`border rounded-lg p-4 ${
        correct ? 'border-green-200 bg-green-50/40' : wrong ? 'border-red-200 bg-red-50/40' : 'border-gray-200'
      }`}
    >
      <div className="flex items-start gap-3 mb-2">
        {correct ? (
          <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
        ) : wrong ? (
          <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
        ) : (
          <AlertCircle className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
        )}
        <div className="flex-1">
          <div className="flex items-center justify-between gap-3 mb-1 flex-wrap">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Question {item.order_index}
              {item.skill_name ? ` · ${item.skill_name}` : ''}
            </span>
            <div className="flex items-center gap-2 flex-wrap">
              {item.answer_kind === 'pseudo_english' && (
                <span className="text-[10px] uppercase font-semibold text-orange-700 bg-orange-100 border border-orange-300 rounded px-1.5 py-0.5">
                  Plain English / pseudocode
                </span>
              )}
              {item.answer_kind === 'blank' && (
                <span className="text-[10px] uppercase font-semibold text-gray-700 bg-gray-100 border border-gray-300 rounded px-1.5 py-0.5">
                  Blank
                </span>
              )}
              <span className="text-xs font-bold text-gray-700">{item.score}/100</span>
            </div>
          </div>
          <p className="text-sm text-gray-800 whitespace-pre-line">{item.question}</p>
          {item.per_skill_scores && Object.keys(item.per_skill_scores).length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {Object.entries(item.per_skill_scores).map(([skill, score]) => (
                <span
                  key={skill}
                  className={`text-[10px] px-2 py-0.5 rounded-full ${
                    score >= 70 ? 'bg-green-100 text-green-800'
                    : score >= 40 ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                  }`}
                >
                  {skill}: {score}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="mt-3 ml-8 grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
        <div>
          <div className="text-[10px] uppercase font-semibold text-gray-500 mb-1">Your answer</div>
          <pre className="bg-white border border-gray-200 rounded p-2 font-mono whitespace-pre-wrap break-all">
            {item.user_answer || '(blank)'}
          </pre>
        </div>
        {item.correct_answer && (
          <div>
            <div className="text-[10px] uppercase font-semibold text-gray-500 mb-1">Correct answer</div>
            <pre className="bg-white border border-gray-200 rounded p-2 font-mono whitespace-pre-wrap break-all">
              {item.correct_answer}
            </pre>
          </div>
        )}
      </div>

      {item.explanation_md && (
        <div className="mt-3 ml-8 text-sm text-gray-800 whitespace-pre-line">
          <span className="text-[10px] uppercase font-semibold text-gray-500 block mb-1">AI feedback</span>
          {item.explanation_md}
        </div>
      )}
    </div>
  );
}
