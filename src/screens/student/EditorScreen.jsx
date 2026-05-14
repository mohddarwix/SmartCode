import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Lightbulb,
  Play,
  RotateCcw,
  Send,
  Terminal,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import Editor from '@monaco-editor/react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { problemsApi } from '../../api/problems';
import { submissionsApi } from '../../api/submissions';
import CheatsheetDrawer from '../../components/CheatsheetDrawer';

const TABS = [
  { id: 'description', label: 'Description' },
  { id: 'solutions',   label: 'Solutions' },
  { id: 'submissions', label: 'Submissions' },
];

const difficultyClass = (d) =>
  d === 'easy'   ? 'text-green-600'  :
  d === 'medium' ? 'text-yellow-600' :
                   'text-red-600';

export default function EditorScreen() {
  const navigate = useNavigate();
  const { id } = useParams();

  const [problem, setProblem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [activeTab, setActiveTab] = useState('description');
  const [consoleTab, setConsoleTab] = useState('testcases');
  const [activeCase, setActiveCase] = useState(0);

  // Run state (transient — not persisted; resets when code changes substantially)
  const [running, setRunning] = useState(false);
  const [runResult, setRunResult] = useState(null);
  const [runError, setRunError] = useState('');

  // Cheatsheet side drawer (per-problem Python syntax reference)
  const [cheatsheetOpen, setCheatsheetOpen] = useState(false);

  // Submit state
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  // Hint state
  const [hint, setHint] = useState(null);
  const [hintLoading, setHintLoading] = useState(false);
  const [hintLevel, setHintLevel] = useState(1);
  const [showHint, setShowHint] = useState(false);
  // { next_hint_index, next_cost_points, total_hints_used, total_cost_so_far, cap_reached, total_cap }
  const [hintPreview, setHintPreview] = useState(null);
  const [hintConfirm, setHintConfirm] = useState(false);

  // Solved-review state: populated only when the user already solved this problem.
  // When non-null, EditorScreen renders a read-only review (no Run / Submit / new hints).
  const [reviewData, setReviewData] = useState(null);

  // History of user's Submit attempts for this problem (newest first). Powers
  // the "Submissions" tab — each row expands to show the code that was sent.
  const [mySubmissions, setMySubmissions] = useState([]);

  const initialCode = useMemo(() => problem?.starter_code_md ?? '', [problem]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setReviewData(null);
    (async () => {
      try {
        const data = await problemsApi.detail(id);
        if (cancelled) return;
        setProblem(data);
        // Past submissions for the Submissions tab — fire-and-forget; tab will
        // show empty until this resolves.
        problemsApi.mySubmissions(id).then((list) => {
          if (!cancelled) setMySubmissions(list || []);
        }).catch(() => {});
        if (data.user_status === 'solved') {
          // Solved — fetch the read-only review payload and skip hint preview / starter code.
          const attempt = await problemsApi.myAttempt(id);
          if (!cancelled) {
            setReviewData(attempt);
            setCode(attempt.submission.code || '');
          }
        } else {
          setCode(data.starter_code_md || '');
          const preview = await problemsApi.hintPreview(id).catch(() => null);
          if (!cancelled && preview) {
            setHintPreview(preview);
            if (preview.total_hints_used) {
              setHintLevel(Math.min(preview.total_hints_used + 1, 3));
            }
          }
        }
      } catch (err) {
        if (!cancelled) setLoadError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const handleReset = () => {
    if (confirm('Reset your code to the starter template?')) {
      setCode(initialCode);
      setRunResult(null);
    }
  };

  // Step 1: user clicks "Request Hint" -> we fetch the cost preview and open the confirm modal.
  const handleRequestHint = async () => {
    setHintLoading(true);
    try {
      const preview = await problemsApi.hintPreview(problem.problem_id);
      setHintPreview(preview);
      setHintConfirm(true);
    } catch (err) {
      setHint({ hint_level: 0, hint_text_md: err.message || 'Could not load hint preview.', source: 'heuristic' });
      setShowHint(true);
    } finally {
      setHintLoading(false);
    }
  };

  // Step 2: user confirms in the modal -> we actually request the LLM hint, paying the cost.
  const handleConfirmHint = async () => {
    setHintConfirm(false);
    setHintLoading(true);
    try {
      const h = await problemsApi.hint(problem.problem_id, { code, language, level: hintLevel });
      setHint(h);
      setShowHint(true);
      setHintLevel((lvl) => Math.min(lvl + 1, 3));
      // Refresh preview so the next request reflects the updated tally
      setHintPreview(await problemsApi.hintPreview(problem.problem_id));
    } catch (err) {
      setHint({ hint_level: 0, hint_text_md: err.message || 'Hint request failed.', source: 'heuristic' });
      setShowHint(true);
    } finally {
      setHintLoading(false);
    }
  };

  const handleRun = async (mode = 'plain') => {
    setRunError('');
    setRunning(true);
    setConsoleTab('result');
    try {
      const apiCall = mode === 'ai'
        ? problemsApi.runWithAi(problem.problem_id, { code, language })
        : problemsApi.run(problem.problem_id, { code, language });
      const result = await apiCall;
      setRunResult(result);
    } catch (err) {
      setRunError(err.message || 'Run failed.');
    } finally {
      setRunning(false);
    }
  };

  const handleSubmit = async () => {
    setSubmitError('');
    setSubmitting(true);
    try {
      const result = await submissionsApi.create({
        problem_id: problem.problem_id,
        code,
        language,
      });
      if (result.status === 'accepted') {
        navigate(`/feedback/${result.submission_id}`);
        return;
      }
      // Strict gate: any failed case denies the submission. Stay on the editor
      // and surface the failures inline; the failed submit was still recorded
      // server-side and now counts double a failed run toward the next score.
      const passed = result.metrics?.passed_count ?? (result.cases || []).filter((c) => c.passed).length;
      const total = result.metrics?.total_count ?? (result.cases || []).length;
      setRunResult({
        cases: result.cases || [],
        passed_count: passed,
        total_count: total,
        all_passed: false,
        status: result.status,
        source: result.grader_source,
        denied: true,
        denial_reason: 'submit',
        score_adjustment: result.score_adjustment,
      });
      setConsoleTab('result');
      setSubmitError(
        `Submission denied: only ${passed}/${total} test cases passed. All tests must pass to submit.`
      );
      // Refresh past submissions list so the new failed attempt appears.
      problemsApi.mySubmissions(problem.problem_id).then(setMySubmissions).catch(() => {});
      setSubmitting(false);
    } catch (err) {
      setSubmitError(err.message || 'Submission failed.');
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
      </div>
    );
  }
  if (loadError || !problem) {
    return (
      <div className="max-w-3xl mx-auto p-8">
        <p className="text-red-700 bg-red-50 border border-red-200 rounded-lg p-4">
          {loadError || 'Problem not found.'}
        </p>
        <Link to="/problems" className="inline-flex items-center text-sm text-indigo-600 mt-4">
          <ArrowLeft className="w-4 h-4 mr-1" /> Back to problems
        </Link>
      </div>
    );
  }

  // Solved-review pre-computed runResult (drives the Test Result tab).
  const reviewRunResult = reviewData
    ? {
        cases: reviewData.submission.cases || [],
        passed_count:
          reviewData.submission.metrics?.passed_count ??
          (reviewData.submission.cases || []).filter((c) => c.passed).length,
        total_count:
          reviewData.submission.metrics?.total_count ??
          (reviewData.submission.cases || []).length,
        all_passed: true,
        status: reviewData.submission.status,
        source: reviewData.submission.grader_source,
      }
    : null;

  return (
    <div className="flex flex-col h-[calc(100vh-65px)] bg-gray-100">
      {/* Top action bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-white border-b">
        <Link to="/problems" className="flex items-center text-sm text-gray-600 hover:text-gray-900">
          <ArrowLeft className="w-4 h-4 mr-1" />
          Problem List
        </Link>
        <div className="flex items-center gap-2">
          {reviewData ? (
            <>
              <span className="flex items-center text-sm font-semibold text-green-700 bg-green-50 border border-green-200 px-3 py-1 rounded">
                <CheckCircle2 className="w-4 h-4 mr-1.5" />
                Solved — Score {reviewData.submission.score}/100
              </span>
              <button
                onClick={() => navigate('/problems')}
                className="bg-indigo-600 text-white px-4 py-1.5 rounded font-medium hover:bg-indigo-700 transition text-sm"
              >
                Back to problems
              </button>
            </>
          ) : (
            <>
              {(runError || submitError) && (
                <span className="text-xs text-red-600 mr-2">{submitError || runError}</span>
              )}
              <button
                onClick={() => handleRun('plain')}
                disabled={running || submitting}
                title="Run your code through Python with no AI commentary (fast smoke test, free)"
                className="bg-gray-200 text-gray-800 px-4 py-1.5 rounded font-medium hover:bg-gray-300 transition flex items-center text-sm disabled:opacity-50"
              >
                <Play className="w-4 h-4 mr-1.5" />
                {running ? 'Running...' : 'Run'}
              </button>
              <button
                onClick={() => handleRun('ai')}
                disabled={running || submitting}
                title="Run + ask the AI for severity, code-quality, and per-case feedback (slower, counts toward score)"
                className="bg-purple-600 text-white px-4 py-1.5 rounded font-medium hover:bg-purple-700 transition flex items-center text-sm disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4 mr-1.5" />
                {running ? 'AI thinking...' : 'Run with AI'}
              </button>
              <button
                onClick={handleSubmit}
                disabled={running || submitting}
                className="bg-green-600 text-white px-4 py-1.5 rounded font-medium hover:bg-green-700 transition flex items-center text-sm disabled:opacity-50"
              >
                <Send className="w-4 h-4 mr-1.5" />
                {submitting ? 'Submitting...' : 'Submit'}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Workspace */}
      <div className="flex-1 overflow-hidden">
        <PanelGroup direction="horizontal" className="h-full">
          <Panel defaultSize={42} minSize={25}>
            <ProblemPanel
              problem={problem}
              activeTab={activeTab}
              setActiveTab={setActiveTab}
              showHint={showHint}
              hint={hint}
              hintLoading={hintLoading}
              onRequestHint={handleRequestHint}
              hintPreview={hintPreview}
              reviewData={reviewData}
              mySubmissions={mySubmissions}
            />
          </Panel>

          <PanelResizeHandle className="w-1.5 bg-gray-200 hover:bg-indigo-400 transition" />

          <Panel defaultSize={58} minSize={30}>
            <PanelGroup direction="vertical" className="h-full">
              <Panel defaultSize={58} minSize={25}>
                <CodePanel
                  code={code}
                  setCode={(v) => { setCode(v); setRunResult(null); }}
                  language={language}
                  setLanguage={setLanguage}
                  onReset={handleReset}
                  readOnly={!!reviewData}
                />
              </Panel>

              <PanelResizeHandle className="h-1.5 bg-gray-200 hover:bg-indigo-400 transition" />

              <Panel defaultSize={42} minSize={20}>
                <ConsolePanel
                  cases={problem.test_cases || []}
                  hasHiddenTests={problem.has_hidden_tests}
                  activeCase={activeCase}
                  setActiveCase={setActiveCase}
                  consoleTab={consoleTab}
                  setConsoleTab={setConsoleTab}
                  runResult={runResult || reviewRunResult}
                  running={running}
                />
              </Panel>
            </PanelGroup>
          </Panel>
        </PanelGroup>
      </div>

      {hintConfirm && hintPreview && (
        <HintConfirmModal
          preview={hintPreview}
          onCancel={() => setHintConfirm(false)}
          onConfirm={handleConfirmHint}
        />
      )}

      <CheatsheetDrawer
        cheatsheetMd={problem?.cheatsheet_md}
        open={cheatsheetOpen}
        onToggle={setCheatsheetOpen}
      />
    </div>
  );
}

function HintConfirmModal({ preview, onCancel, onConfirm }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full mx-4 p-6">
        <div className="flex items-start gap-3">
          <div className="bg-yellow-100 rounded-full p-2">
            <Lightbulb className="w-5 h-5 text-yellow-600" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900">
              Request hint #{preview.next_hint_index}?
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              This hint will deduct{' '}
              <span className="font-semibold text-red-600">
                -{preview.next_cost_points} points
              </span>{' '}
              from your final score when you submit. Hints get more expensive as you ask
              for more (3, 5, 8, ... up to a cap of {preview.total_cap} points per problem).
            </p>
            {preview.total_hints_used > 0 && (
              <p className="text-xs text-gray-500 mt-2">
                Already used {preview.total_hints_used} hint
                {preview.total_hints_used === 1 ? '' : 's'} — {preview.total_cost_so_far}{' '}
                points deducted so far. After this hint, total cost will be{' '}
                {Math.min(preview.total_cap, preview.total_cost_so_far + preview.next_cost_points)}{' '}
                points.
              </p>
            )}
            <p className="text-xs text-gray-600 mt-3 italic">
              The AI will look at your current code and tailor the hint to what
              you've written so far.
            </p>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700"
          >
            Yes, take the hint
          </button>
        </div>
      </div>
    </div>
  );
}

// ===========================================================================
// Left: Problem description panel (with tabs)
// ===========================================================================
function ProblemPanel({ problem, activeTab, setActiveTab, showHint, hint, hintLoading, onRequestHint, hintPreview, reviewData, mySubmissions }) {
  return (
    <div className="flex flex-col h-full bg-white">
      <div className="flex border-b bg-gray-50 px-2">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`px-4 py-2.5 text-sm font-medium transition border-b-2 ${
              activeTab === t.id
                ? 'border-indigo-600 text-indigo-700'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'description' && (
          <DescriptionTab
            problem={problem}
            showHint={showHint}
            hint={hint}
            hintLoading={hintLoading}
            onRequestHint={onRequestHint}
            hintPreview={hintPreview}
            reviewData={reviewData}
          />
        )}
        {activeTab === 'solutions' && (
          <SolutionsTab problem={problem} reviewData={reviewData} />
        )}
        {activeTab === 'submissions' && (
          <SubmissionsTab submissions={mySubmissions} />
        )}
      </div>
    </div>
  );
}

function DescriptionTab({ problem, showHint, hint, hintLoading, onRequestHint, hintPreview, reviewData }) {
  const sampleCases = (problem.test_cases || []).filter((c) => c.visibility === 'sample');
  return (
    <div className="space-y-5">
      {reviewData && <SolvedBanner reviewData={reviewData} />}
      <h1 className="text-xl font-bold text-gray-900">
        {problem.problem_id}. {problem.title}
      </h1>
      <div className="flex items-center gap-3 text-xs">
        <span className={`font-semibold ${difficultyClass(problem.difficulty)}`}>
          {capitalize(problem.difficulty)}
        </span>
        {problem.source && (
          <>
            <span className="text-gray-400">|</span>
            <span className="text-gray-500">{problem.source}</span>
          </>
        )}
        {problem.skills?.length > 0 && (
          <>
            <span className="text-gray-400">|</span>
            <span className="text-gray-500">{problem.skills.join(', ')}</span>
          </>
        )}
      </div>

      <p className="text-gray-800 whitespace-pre-line leading-relaxed">{problem.statement_md}</p>

      {sampleCases.map((c, i) => (
        <div key={i}>
          <h3 className="font-semibold text-gray-900 mb-2">Example {i + 1}:</h3>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm font-mono whitespace-pre-wrap">
            <div><span className="text-gray-500">Input:</span> {c.input_blob}</div>
            <div><span className="text-gray-500">Output:</span> {c.expected_blob}</div>
          </div>
        </div>
      ))}

      {problem.constraints_md && (
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Constraints:</h3>
          <pre className="text-xs text-gray-800 whitespace-pre-wrap font-mono bg-gray-50 border border-gray-200 rounded p-3">
            {problem.constraints_md}
          </pre>
        </div>
      )}

      {reviewData ? (
        <SolvedReviewSections reviewData={reviewData} />
      ) : (
        <>
          {showHint && hint && (
            <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-r">
              <div className="flex items-start">
                <Lightbulb className="w-5 h-5 text-yellow-600 mr-2 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-semibold text-yellow-900 flex items-center gap-2">
                    Hint {hint.hint_level > 0 ? `Level ${hint.hint_level}` : ''}
                    {hint.source === 'heuristic' && (
                      <span className="text-[10px] uppercase tracking-wide font-normal text-yellow-700">
                        fallback
                      </span>
                    )}
                  </h4>
                  <p className="text-sm text-yellow-800 mt-1 whitespace-pre-line">{hint.hint_text_md}</p>
                </div>
              </div>
            </div>
          )}

          <div className="flex items-center gap-3 flex-wrap">
            <button
              onClick={onRequestHint}
              disabled={hintLoading || hintPreview?.cap_reached}
              className="text-indigo-600 hover:text-indigo-700 font-medium text-sm flex items-center gap-1.5 disabled:opacity-50"
            >
              <Lightbulb className="w-4 h-4" />
              {hintLoading
                ? 'Loading hint...'
                : hintPreview?.cap_reached
                ? 'Hint cap reached'
                : `Request hint${
                    hintPreview ? ` (-${hintPreview.next_cost_points} pts)` : ''
                  }`}
            </button>
            {hintPreview && hintPreview.total_hints_used > 0 && (
              <span className="text-xs text-gray-500">
                Used {hintPreview.total_hints_used} hint
                {hintPreview.total_hints_used === 1 ? '' : 's'} so far — total {hintPreview.total_cost_so_far}/
                {hintPreview.total_cap} points will be deducted on submit
              </span>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function SolvedBanner({ reviewData }) {
  const s = reviewData.submission;
  const when = new Date(s.submitted_at).toLocaleDateString();
  return (
    <div className="bg-green-50 border-l-4 border-green-600 p-4 rounded-r">
      <div className="flex items-start gap-3">
        <CheckCircle2 className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="font-semibold text-green-900">
            You solved this problem on {when} - score {s.score}/100
          </p>
          <p className="text-sm text-green-800 mt-1">
            This view is read-only. You can no longer Run, Submit, or request new
            hints. Browse your code on the right and the feedback + hint history below.
          </p>
        </div>
      </div>
    </div>
  );
}

function SolvedReviewSections({ reviewData }) {
  const s = reviewData.submission;
  return (
    <div className="space-y-4">
      {s.feedback_summary_md && (
        <div className="bg-blue-50 border-l-4 border-blue-600 p-4 rounded-r">
          <h3 className="font-semibold text-blue-900 mb-1">AI feedback</h3>
          <p className="text-sm text-blue-900">{s.feedback_summary_md}</p>
          {s.feedback_bullets?.length > 0 && (
            <ul className="text-sm text-blue-800 mt-2 space-y-1">
              {s.feedback_bullets.map((b, i) => (
                <li key={i}>{b.kind === 'good' ? '+' : '!'} {b.text}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {reviewData.hints.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded p-3 text-sm text-gray-600">
          You solved this problem without requesting any hints. Nice.
        </div>
      ) : (
        <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-r">
          <h3 className="font-semibold text-yellow-900 mb-2 flex items-center gap-2">
            <Lightbulb className="w-5 h-5" />
            Hints used ({reviewData.hints.length}) — total cost {reviewData.hint_total_cost} points
          </h3>
          <ol className="space-y-3">
            {reviewData.hints.map((h, i) => (
              <li key={i} className="text-sm text-yellow-900">
                <span className="font-semibold">Hint #{i + 1} (level {h.hint_level}):</span>{' '}
                <span className="whitespace-pre-line">{h.hint_text_md}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

function EmptyTab({ title, message }) {
  return (
    <div className="text-center text-gray-500 py-16">
      <Terminal className="w-10 h-10 mx-auto text-gray-300 mb-3" />
      <h3 className="font-semibold text-gray-700">{title}</h3>
      <p className="text-sm mt-1 max-w-sm mx-auto">{message}</p>
    </div>
  );
}

function SolutionsTab({ problem, reviewData }) {
  // Interactive step-by-step AI tutor (chat-style).
  // `reviewData` is accepted for symmetry with other tabs but not used here.
  const [history, setHistory] = useState([]);          // [{role: 'tutor'|'student', content, step_index?}, ...]
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [stepIndex, setStepIndex] = useState(0);       // 0 until tutor sends first turn
  const [totalSteps, setTotalSteps] = useState(6);
  const [complete, setComplete] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [history, busy]);

  // Send a turn. Pass null for the very first call.
  const sendTurn = async (studentMessage) => {
    setBusy(true);
    setError('');
    try {
      const wireHistory = history.map((m) => ({
        role: m.role,
        content: m.content,
        step_index: m.step_index ?? null,
      }));
      const turn = await problemsApi.tutorTurn(problem.problem_id, {
        history: wireHistory,
        studentMessage,
      });
      // Append student turn (if any) + tutor turn
      setHistory((prev) => {
        const next = [...prev];
        if (studentMessage) next.push({ role: 'student', content: studentMessage });
        next.push({
          role: 'tutor',
          content: turn.tutor_response,
          step_index: turn.step_index,
        });
        return next;
      });
      setStepIndex(turn.step_index);
      setTotalSteps(turn.total_steps);
      setComplete(turn.is_complete);
    } catch (err) {
      setError(err.message || 'AI tutor turn failed.');
    } finally {
      setBusy(false);
    }
  };

  const startSession = () => {
    setHistory([]);
    setComplete(false);
    setError('');
    sendTurn(null);
  };

  const submitReply = (e) => {
    e?.preventDefault?.();
    const text = input.trim();
    if (!text || busy || complete) return;
    setInput('');
    sendTurn(text);
  };

  const tutorStarted = history.length > 0;

  return (
    <div className="space-y-4 flex flex-col h-full">
      <div className="bg-indigo-50 border-l-4 border-indigo-600 p-4 rounded-r">
        <h3 className="font-semibold text-indigo-900 flex items-center gap-2">
          <Sparkles className="w-5 h-5" />
          Step-by-step AI tutor
        </h3>
        <p className="text-sm text-indigo-800 mt-1">
          A patient tutor walks you through this problem one step at a time and
          checks your understanding after each. You decide the pace.
        </p>
        <div className="mt-3 flex items-center gap-2 flex-wrap">
          {!tutorStarted && !busy && (
            <button
              onClick={startSession}
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 transition flex items-center gap-2 text-sm"
            >
              <Sparkles className="w-4 h-4" />
              Start tutor session
            </button>
          )}
          {tutorStarted && (
            <>
              <span className="text-xs text-indigo-700 font-medium">
                Step {stepIndex} of {totalSteps}
              </span>
              <div className="flex-1 max-w-xs bg-indigo-100 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-indigo-600 h-full transition-all"
                  style={{ width: `${Math.min(100, (stepIndex / totalSteps) * 100)}%` }}
                />
              </div>
              {!busy && (
                <button
                  onClick={startSession}
                  className="text-xs text-indigo-700 underline hover:text-indigo-900"
                  title="Reset the conversation and start over"
                >
                  Restart
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {tutorStarted && (
        <>
          <div
            ref={scrollRef}
            className="bg-white border border-gray-200 rounded-lg p-3 flex-1 min-h-[300px] max-h-[55vh] overflow-y-auto space-y-3"
          >
            {history.map((m, idx) => (
              <TutorBubble key={idx} role={m.role} content={m.content} stepIndex={m.step_index} />
            ))}
            {busy && (
              <div className="flex items-center gap-2 text-xs text-indigo-600 px-1">
                <Sparkles className="w-3 h-3 animate-pulse" />
                <span>Tutor is thinking...</span>
              </div>
            )}
            {complete && !busy && (
              <div className="bg-green-50 border border-green-200 rounded p-3 text-sm text-green-800 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>Lesson complete. You can try the problem now in the editor on the right.</span>
              </div>
            )}
          </div>

          {!complete && (
            <form onSubmit={submitReply} className="flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={busy ? 'Tutor is thinking...' : 'Type your answer...'}
                disabled={busy}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none disabled:bg-gray-50"
                autoFocus
              />
              <button
                type="submit"
                disabled={busy || !input.trim()}
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 transition flex items-center gap-1 text-sm disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
                Send
              </button>
            </form>
          )}
        </>
      )}
    </div>
  );
}

function TutorBubble({ role, content, stepIndex }) {
  const isTutor = role === 'tutor';
  return (
    <div className={`flex ${isTutor ? 'justify-start' : 'justify-end'}`}>
      <div
        className={`max-w-[88%] rounded-lg px-3 py-2 text-sm ${
          isTutor
            ? 'bg-indigo-50 border border-indigo-100 text-gray-800'
            : 'bg-gray-100 border border-gray-200 text-gray-800'
        }`}
      >
        {isTutor && stepIndex && (
          <div className="text-[10px] uppercase tracking-wider text-indigo-700 font-semibold mb-1">
            Tutor - step {stepIndex}
          </div>
        )}
        <TutorMarkdown text={content} />
      </div>
    </div>
  );
}

function TutorMarkdown({ text }) {
  // Reuse the same line+fence parser as the cheatsheet drawer / streamed transcript,
  // but tuned for chat bubbles: keep paragraphs tight.
  const blocks = parseStreamedMarkdown(text);
  return (
    <div className="space-y-2">
      {blocks.map((b, i) => {
        if (b.kind === 'h2' || b.kind === 'h3') {
          return <p key={i} className="font-semibold text-indigo-800">{b.text}</p>;
        }
        if (b.kind === 'code') {
          return (
            <pre
              key={i}
              className="bg-gray-900 text-green-300 text-xs font-mono p-2 rounded overflow-x-auto whitespace-pre"
            >
              {b.text}
            </pre>
          );
        }
        return <p key={i} className="whitespace-pre-line">{b.text}</p>;
      })}
    </div>
  );
}

/**
 * Render the streamed markdown text:
 *   - Lines starting with "## " or "### " become headings
 *   - Triple-backtick fences become dark code blocks
 *   - Everything else is rendered as paragraphs
 *
 * Tolerant of incomplete input — an unclosed code fence at the end is rendered
 * as a still-streaming code block.
 */
function StreamedTranscript({ text, streaming }) {
  const blocks = parseStreamedMarkdown(text);
  return (
    <div className="space-y-3 text-sm text-gray-800">
      {blocks.map((b, i) => {
        if (b.kind === 'h2') {
          return <h2 key={i} className="text-base font-bold text-indigo-700 mt-4">{b.text}</h2>;
        }
        if (b.kind === 'h3') {
          return <h3 key={i} className="text-sm font-semibold text-gray-800 mt-3">{b.text}</h3>;
        }
        if (b.kind === 'code') {
          return (
            <pre
              key={i}
              className="bg-[#1e1e1e] text-gray-100 text-xs font-mono p-3 rounded overflow-x-auto whitespace-pre"
            >
              {b.text}
              {b.unclosed && streaming && <span className="text-indigo-400">_</span>}
            </pre>
          );
        }
        return (
          <p key={i} className="whitespace-pre-line leading-relaxed">{b.text}</p>
        );
      })}
    </div>
  );
}

function parseStreamedMarkdown(text) {
  const blocks = [];
  let i = 0;
  let buf = '';
  const flushPara = () => {
    if (buf.trim()) blocks.push({ kind: 'p', text: buf.trim() });
    buf = '';
  };
  const lines = text.split('\n');
  for (let li = 0; li < lines.length; li++) {
    const line = lines[li];
    if (line.startsWith('```')) {
      flushPara();
      // collect until next ``` or end
      const fenceParts = [];
      li++;
      while (li < lines.length && !lines[li].startsWith('```')) {
        fenceParts.push(lines[li]);
        li++;
      }
      const unclosed = li >= lines.length; // hit end without closing fence
      blocks.push({ kind: 'code', text: fenceParts.join('\n'), unclosed });
      continue;
    }
    if (line.startsWith('## ')) {
      flushPara();
      blocks.push({ kind: 'h2', text: line.slice(3).trim() });
      continue;
    }
    if (line.startsWith('### ')) {
      flushPara();
      blocks.push({ kind: 'h3', text: line.slice(4).trim() });
      continue;
    }
    if (line.trim() === '') {
      flushPara();
      continue;
    }
    buf += (buf ? '\n' : '') + line;
  }
  flushPara();
  return blocks;
}

function SubmissionsTab({ submissions }) {
  const [expandedId, setExpandedId] = useState(null);

  if (!submissions || submissions.length === 0) {
    return (
      <EmptyTab
        title="No submissions yet"
        message="Hit Submit on this problem and your attempts will show up here, newest first."
      />
    );
  }

  const fmt = (iso) => {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  };

  const statusClass = (s) =>
    s === 'accepted'
      ? 'text-green-700 bg-green-100'
      : s === 'wrong_answer'
      ? 'text-red-700 bg-red-100'
      : 'text-gray-700 bg-gray-100';

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-gray-700 mb-1">
        Your submissions ({submissions.length})
      </h3>
      {submissions.map((s) => {
        const open = expandedId === s.submission_id;
        return (
          <div key={s.submission_id} className="border border-gray-200 rounded-lg overflow-hidden">
            <button
              type="button"
              onClick={() => setExpandedId(open ? null : s.submission_id)}
              className="w-full flex items-center justify-between px-3 py-2 bg-white hover:bg-gray-50 text-left"
            >
              <span className="flex items-center gap-3 text-sm">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${statusClass(s.status)}`}>
                  {s.status.replace('_', ' ')}
                </span>
                <span className="font-mono text-xs text-gray-500">
                  {s.passed_count != null && s.total_count != null
                    ? `${s.passed_count}/${s.total_count}`
                    : '-/-'}
                </span>
                <span className="text-xs text-gray-700">{fmt(s.submitted_at)}</span>
              </span>
              <span className="flex items-center gap-3">
                <span className="text-sm font-semibold text-gray-800">{s.score}/100</span>
                <span className="text-xs text-gray-400">{open ? '▲' : '▼'}</span>
              </span>
            </button>
            {open && (
              <pre className="bg-[#1e1e1e] text-gray-100 text-xs font-mono p-3 overflow-x-auto whitespace-pre">
                {s.code}
              </pre>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ===========================================================================
// Top right: Code editor panel (Monaco)
// ===========================================================================
function CodePanel({ code, setCode, language, setLanguage, onReset, readOnly = false }) {
  return (
    <div className="flex flex-col h-full bg-[#1e1e1e]">
      <div className="flex items-center justify-between px-3 py-2 bg-[#252526] border-b border-black/30">
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          disabled={readOnly}
          className="bg-[#3c3c3c] text-gray-200 text-xs px-2 py-1 rounded border border-black/30 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-60"
        >
          <option value="python">Python 3</option>
          <option value="javascript" disabled>JavaScript (soon)</option>
          <option value="java" disabled>Java (soon)</option>
          <option value="cpp" disabled>C++ (soon)</option>
        </select>
        {readOnly ? (
          <span className="text-[10px] uppercase tracking-wide text-green-400">Read-only — your accepted code</span>
        ) : (
          <button
            onClick={onReset}
            title="Reset to starter code"
            className="text-gray-400 hover:text-gray-200 p-1.5 rounded hover:bg-white/10"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="flex-1 min-h-0">
        <Editor
          value={code}
          onChange={(v) => setCode(v ?? '')}
          language="python"
          theme="vs-dark"
          options={{
            readOnly,
            fontSize: 14,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontFamily: '"Fira Code", "Cascadia Code", "Menlo", "Consolas", monospace',
            fontLigatures: true,
            automaticLayout: true,
            tabSize: 4,
            padding: { top: 12, bottom: 12 },
            renderLineHighlight: 'gutter',
            smoothScrolling: true,
          }}
          loading={<div className="text-gray-400 p-4 text-sm">Loading editor...</div>}
        />
      </div>
    </div>
  );
}

// ===========================================================================
// Bottom right: Test cases / Test results panel
// ===========================================================================
function ConsolePanel({ cases, hasHiddenTests, activeCase, setActiveCase, consoleTab, setConsoleTab, runResult, running }) {
  const current = cases[activeCase];
  const passedCount = runResult?.passed_count ?? 0;
  const totalCount = runResult?.total_count ?? 0;

  return (
    <div className="flex flex-col h-full bg-white border-t border-gray-200">
      <div className="flex items-center justify-between border-b bg-gray-50 px-2">
        <div className="flex">
          <ConsoleTab
            active={consoleTab === 'testcases'}
            onClick={() => setConsoleTab('testcases')}
            label="Testcase"
          />
          <ConsoleTab
            active={consoleTab === 'result'}
            onClick={() => setConsoleTab('result')}
            label="Test Result"
            badge={
              runResult ? (
                <span
                  className={`ml-2 inline-flex items-center text-[10px] font-semibold rounded-full px-1.5 ${
                    runResult.all_passed
                      ? 'bg-green-100 text-green-700'
                      : 'bg-red-100 text-red-700'
                  }`}
                >
                  {passedCount}/{totalCount}
                </span>
              ) : null
            }
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {consoleTab === 'testcases' ? (
          <TestcasesView
            cases={cases}
            hasHiddenTests={hasHiddenTests}
            activeCase={activeCase}
            setActiveCase={setActiveCase}
            current={current}
          />
        ) : (
          <TestResultView runResult={runResult} running={running} />
        )}
      </div>
    </div>
  );
}

function ConsoleTab({ active, onClick, label, badge }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium transition border-b-2 flex items-center ${
        active
          ? 'border-indigo-600 text-indigo-700'
          : 'border-transparent text-gray-600 hover:text-gray-900'
      }`}
    >
      {label}
      {badge}
    </button>
  );
}

function TestcasesView({ cases, hasHiddenTests, activeCase, setActiveCase, current }) {
  if (cases.length === 0) {
    return <p className="text-sm text-gray-500">No visible test cases for this problem.</p>;
  }
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-1.5 flex-wrap">
        {cases.map((c, i) => (
          <button
            key={i}
            onClick={() => setActiveCase(i)}
            className={`text-xs px-3 py-1 rounded-full transition ${
              i === activeCase
                ? 'bg-gray-900 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Case {i + 1}
          </button>
        ))}
        {hasHiddenTests && (
          <span className="text-[10px] uppercase tracking-wide text-gray-400 ml-2">
            + hidden tests run on submit
          </span>
        )}
      </div>
      <div>
        <label className="block text-xs font-semibold text-gray-500 mb-1">Input</label>
        <pre className="bg-gray-50 border border-gray-200 rounded p-3 text-sm font-mono whitespace-pre-wrap">
          {current.input_blob}
        </pre>
      </div>
      <div>
        <label className="block text-xs font-semibold text-gray-500 mb-1">Expected</label>
        <pre className="bg-gray-50 border border-gray-200 rounded p-3 text-sm font-mono whitespace-pre-wrap">
          {current.expected_blob}
        </pre>
      </div>
    </div>
  );
}

function TestResultView({ runResult, running }) {
  if (running) {
    return (
      <div className="flex items-center justify-center py-8 text-gray-500 text-sm gap-2">
        <Sparkles className="w-4 h-4 text-indigo-500 animate-pulse" />
        AI is evaluating your code against the visible test cases...
      </div>
    );
  }
  if (!runResult) {
    return (
      <p className="text-sm text-gray-500">
        Click <strong>Run</strong> to test your code against the visible test cases.
        The AI will tell you what each case produced and explain any failures.
      </p>
    );
  }
  const adj = runResult.score_adjustment;
  return (
    <div className="space-y-3">
      {runResult.denied && (
        <div className="bg-red-50 border-l-4 border-red-600 p-3 rounded-r">
          <p className="text-sm font-semibold text-red-900 flex items-center gap-2">
            <XCircle className="w-4 h-4" />
            Submission denied — all test cases must pass.
          </p>
          <p className="text-xs text-red-800 mt-1">
            This failed submit was logged and will deduct points from your final score
            when you eventually pass. Failed submits weigh 2x failed runs.
          </p>
          {adj && (
            <p className="text-[11px] text-red-700 mt-1">
              Current accumulated penalty: {adj.penalty_points} severity points across{' '}
              {adj.prior_failed_attempts} prior failed{' '}
              {adj.prior_failed_attempts === 1 ? 'attempt' : 'attempts'}.
            </p>
          )}
        </div>
      )}
      {!runResult.denied && !runResult.all_passed && (
        <div className="bg-amber-50 border-l-4 border-amber-500 p-3 rounded-r">
          <p className="text-xs text-amber-900">
            <strong>Heads up:</strong> failed runs are recorded and will reduce your
            final score (each failed visible case adds severity points at 0.5x weight).
            Fix the failures before submitting.
          </p>
        </div>
      )}
      <CaseResultsList result={runResult} />
    </div>
  );
}

// Reusable per-case list (also used on FeedbackScreen).
export function CaseResultsList({ result }) {
  const allPassed = result.all_passed ?? (result.passed_count === result.total_count);
  return (
    <div className="space-y-3">
      <div
        className={`flex items-center gap-2 text-sm font-semibold ${
          allPassed ? 'text-green-700' : 'text-red-700'
        }`}
      >
        {allPassed ? (
          <CheckCircle2 className="w-5 h-5" />
        ) : (
          <XCircle className="w-5 h-5" />
        )}
        {allPassed ? 'All test cases passed' : `${result.passed_count}/${result.total_count} test cases passed`}
        {result.source === 'sandbox' && (
          <span className="ml-2 text-[10px] uppercase font-normal text-gray-500">plain run -- no AI commentary</span>
        )}
        {result.source === 'heuristic' && (
          <span className="ml-2 text-[10px] uppercase font-normal text-gray-500">heuristic only (AI offline)</span>
        )}
      </div>

      <div className="space-y-2">
        {result.cases.map((c) => (
          <CaseResultRow key={c.case_index} c={c} />
        ))}
      </div>
    </div>
  );
}

function CaseResultRow({ c }) {
  return (
    <div
      className={`border rounded-lg overflow-hidden ${
        c.passed ? 'border-green-200 bg-green-50/40' : 'border-red-200 bg-red-50/40'
      }`}
    >
      <div
        className={`px-3 py-1.5 text-xs font-semibold flex items-center justify-between ${
          c.passed ? 'text-green-800' : 'text-red-800'
        }`}
      >
        <span className="flex items-center gap-1.5">
          {c.passed ? (
            <CheckCircle2 className="w-4 h-4" />
          ) : (
            <XCircle className="w-4 h-4" />
          )}
          Case {c.case_index} — {c.passed ? 'Passed' : 'Failed'}
        </span>
        <span className="flex items-center gap-2">
          {!c.passed && c.severity && <SeverityBadge severity={c.severity} />}
          <span className="text-[10px] uppercase tracking-wide opacity-70">{c.visibility}</span>
        </span>
      </div>
      <div className="px-3 pb-2 pt-1 grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
        <Field label="Input" value={c.input_blob} />
        <Field label="Expected" value={c.expected_blob} />
        <Field label="Your output" value={c.predicted_output || '(no output)'} highlight={!c.passed} />
      </div>
      {c.explanation_md && !c.passed && (
        <div className="px-3 pb-3 text-xs text-red-900 bg-red-50 border-t border-red-200">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
            <span className="whitespace-pre-line">{c.explanation_md}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export function SeverityBadge({ severity }) {
  const styles =
    severity === 'severe'
      ? 'bg-red-200 text-red-900 border-red-300'
      : severity === 'moderate'
      ? 'bg-orange-200 text-orange-900 border-orange-300'
      : 'bg-yellow-100 text-yellow-900 border-yellow-300';
  return (
    <span
      className={`text-[10px] uppercase tracking-wide font-semibold border rounded px-1.5 py-0.5 ${styles}`}
      title={
        severity === 'severe'
          ? 'Major bug — fundamental logic or crash'
          : severity === 'moderate'
          ? 'Missed edge case or partial logic gap'
          : 'Minor mismatch — likely cosmetic'
      }
    >
      {severity}
    </span>
  );
}

function Field({ label, value, highlight }) {
  return (
    <div>
      <div className="text-[10px] uppercase text-gray-500 font-semibold mb-0.5">{label}</div>
      <pre
        className={`font-mono rounded px-2 py-1 whitespace-pre-wrap break-all text-xs ${
          highlight ? 'bg-red-100 text-red-900' : 'bg-white text-gray-800'
        }`}
      >
        {value}
      </pre>
    </div>
  );
}

function capitalize(s) {
  return s ? s[0].toUpperCase() + s.slice(1) : s;
}
