import { useEffect, useState } from 'react';
import { Plus, Pencil, Trash2, Search, AlertCircle, FlaskConical, X, Save } from 'lucide-react';
import { adminApi } from '../../api/admin';
import { skillsApi } from '../../api/skills';

const difficultyClass = (d) =>
  d === 'easy'   ? 'bg-green-100 text-green-700'  :
  d === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                   'bg-red-100 text-red-700';

export default function AdminProblemsScreen() {
  const [problems, setProblems] = useState([]);
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [testCasesForProblem, setTestCasesForProblem] = useState(null); // {problem_id, title}

  const load = () => {
    setLoading(true);
    Promise.all([adminApi.listProblems(), skillsApi.catalog()])
      .then(([ps, sk]) => {
        setProblems(ps);
        setSkills(sk);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const filtered = problems.filter(
    (p) =>
      p.title.toLowerCase().includes(query.toLowerCase()) ||
      p.skills.join(',').toLowerCase().includes(query.toLowerCase()),
  );

  const handleSave = async (data) => {
    try {
      if (editing) {
        await adminApi.updateProblem(editing.problem_id, data);
      } else {
        await adminApi.createProblem(data);
      }
      setShowForm(false);
      setEditing(null);
      load();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this problem?')) return;
    try {
      await adminApi.deleteProblem(id);
      load();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Problems</h1>
          <p className="text-gray-600 text-sm">Add, edit, and remove programming problems.</p>
        </div>
        <button
          onClick={() => { setEditing(null); setShowForm(true); }}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 transition flex items-center"
        >
          <Plus className="w-4 h-4 mr-1" /> New problem
        </button>
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
            placeholder="Search by title or skill..."
            className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-md overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
            <tr>
              <th className="text-left px-4 py-3">#</th>
              <th className="text-left px-4 py-3">Title</th>
              <th className="text-left px-4 py-3">Difficulty</th>
              <th className="text-left px-4 py-3 hidden lg:table-cell">Skills</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-right px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={6} className="text-center text-gray-500 py-8">Loading...</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={6} className="text-center text-gray-500 py-8">No problems match your search.</td></tr>
            ) : (
              filtered.map((p) => (
                <tr key={p.problem_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-600">{p.problem_id}</td>
                  <td className="px-4 py-3 font-medium text-gray-800">{p.title}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs ${difficultyClass(p.difficulty)}`}>
                      {capitalize(p.difficulty)}
                    </span>
                  </td>
                  <td className="px-4 py-3 hidden lg:table-cell text-gray-600">{p.skills.join(', ')}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs ${p.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-700'}`}>
                      {p.is_active ? 'Active' : 'Hidden'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      <button
                        onClick={() => setTestCasesForProblem({ problem_id: p.problem_id, title: p.title })}
                        className="p-2 text-gray-600 hover:text-purple-600 hover:bg-purple-50 rounded"
                        title="Test cases"
                      >
                        <FlaskConical className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => { setEditing(p); setShowForm(true); }}
                        className="p-2 text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 rounded"
                        title="Edit"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(p.problem_id)}
                        className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showForm && (
        <ProblemForm
          initial={editing}
          skills={skills}
          onCancel={() => { setShowForm(false); setEditing(null); }}
          onSave={handleSave}
        />
      )}

      {testCasesForProblem && (
        <TestCasesEditor
          problemId={testCasesForProblem.problem_id}
          problemTitle={testCasesForProblem.title}
          onClose={() => setTestCasesForProblem(null)}
        />
      )}
    </div>
  );
}

// ===========================================================================
// Test-case editor modal (FR-Admin 2: admins can manage test cases via UI)
// ===========================================================================
function TestCasesEditor({ problemId, problemTitle, onClose }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [draft, setDraft] = useState(null); // null | { test_case_id?, name, visibility, input_blob, expected_blob }

  const load = () => {
    setLoading(true);
    adminApi.listTestCases(problemId)
      .then((rows) => { setCases(rows); setError(''); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };
  useEffect(load, [problemId]);

  const handleSave = async () => {
    if (!draft.input_blob.trim() || !draft.expected_blob.trim()) {
      setError('Input and expected output are both required.');
      return;
    }
    try {
      if (draft.test_case_id) {
        await adminApi.updateTestCase(draft.test_case_id, {
          name: draft.name || null,
          visibility: draft.visibility,
          input_blob: draft.input_blob,
          expected_blob: draft.expected_blob,
        });
      } else {
        await adminApi.createTestCase(problemId, {
          name: draft.name || null,
          visibility: draft.visibility,
          input_blob: draft.input_blob,
          expected_blob: draft.expected_blob,
        });
      }
      setDraft(null);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (tcId) => {
    if (!confirm('Delete this test case? The grader will no longer evaluate against it.')) return;
    try {
      await adminApi.deleteTestCase(tcId);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const visibilityColor = (v) =>
    v === 'sample' ? 'bg-blue-100 text-blue-700' :
    v === 'public' ? 'bg-green-100 text-green-700' :
                     'bg-gray-200 text-gray-700';

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div>
            <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
              <FlaskConical className="w-5 h-5 text-purple-600" />
              Test cases for &ldquo;{problemTitle}&rdquo;
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              <span className="font-medium">sample</span> = shown in description.
              {' '}<span className="font-medium">public</span> = visible in editor before submit.
              {' '}<span className="font-medium">hidden</span> = only revealed on submit.
            </p>
          </div>
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

        <div className="flex-1 overflow-y-auto p-6 space-y-3">
          {loading ? (
            <div className="text-center text-gray-500 py-8">Loading...</div>
          ) : cases.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              No test cases yet. Click "Add test case" to create one.
            </div>
          ) : cases.map((tc) => (
            <div key={tc.test_case_id} className="border border-gray-200 rounded-lg p-3">
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-semibold text-gray-700">#{tc.test_case_id}</span>
                  {tc.name && <span className="text-sm font-medium text-gray-800">{tc.name}</span>}
                  <span className={`text-[10px] uppercase px-2 py-0.5 rounded ${visibilityColor(tc.visibility)}`}>
                    {tc.visibility}
                  </span>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => setDraft({ ...tc })}
                    className="p-1.5 text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 rounded"
                    title="Edit"
                  >
                    <Pencil className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => handleDelete(tc.test_case_id)}
                    className="p-1.5 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded"
                    title="Delete"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono">
                <div>
                  <div className="text-[10px] uppercase font-semibold text-gray-500 mb-0.5">Input</div>
                  <pre className="bg-gray-50 border border-gray-200 rounded p-2 whitespace-pre-wrap break-all max-h-32 overflow-y-auto">{tc.input_blob}</pre>
                </div>
                <div>
                  <div className="text-[10px] uppercase font-semibold text-gray-500 mb-0.5">Expected</div>
                  <pre className="bg-gray-50 border border-gray-200 rounded p-2 whitespace-pre-wrap break-all max-h-32 overflow-y-auto">{tc.expected_blob}</pre>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="px-6 py-3 border-t bg-gray-50 flex justify-between">
          <button
            onClick={() => setDraft({ name: '', visibility: 'hidden', input_blob: '', expected_blob: '' })}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 transition flex items-center"
          >
            <Plus className="w-4 h-4 mr-1" /> Add test case
          </button>
          <button onClick={onClose} className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded">
            Done
          </button>
        </div>

        {draft && (
          <TestCaseDraftModal
            draft={draft}
            setDraft={setDraft}
            onCancel={() => setDraft(null)}
            onSave={handleSave}
          />
        )}
      </div>
    </div>
  );
}

function TestCaseDraftModal({ draft, setDraft, onCancel, onSave }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg p-5">
        <h3 className="font-bold text-gray-800 mb-3">
          {draft.test_case_id ? `Edit test case #${draft.test_case_id}` : 'New test case'}
        </h3>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Name (optional)</label>
            <input
              value={draft.name || ''}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              placeholder="e.g. 'duplicates' or 'empty array'"
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Visibility</label>
            <select
              value={draft.visibility}
              onChange={(e) => setDraft({ ...draft, visibility: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white focus:ring-2 focus:ring-indigo-500"
            >
              <option value="sample">sample (shown in problem description)</option>
              <option value="public">public (visible before submit)</option>
              <option value="hidden">hidden (only used at submit)</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Input</label>
            <textarea
              value={draft.input_blob}
              onChange={(e) => setDraft({ ...draft, input_blob: e.target.value })}
              placeholder={'nums = [2,7,11,15]\ntarget = 9'}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm font-mono focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Expected output</label>
            <textarea
              value={draft.expected_blob}
              onChange={(e) => setDraft({ ...draft, expected_blob: e.target.value })}
              placeholder="[0,1]"
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm font-mono focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-4">
          <button onClick={onCancel} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded">Cancel</button>
          <button
            onClick={onSave}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 flex items-center"
          >
            <Save className="w-4 h-4 mr-1" /> Save
          </button>
        </div>
      </div>
    </div>
  );
}

function ProblemForm({ initial, skills, onCancel, onSave }) {
  const [form, setForm] = useState(
    initial
      ? {
          slug: initial.slug,
          title: initial.title,
          difficulty: initial.difficulty,
          source: initial.source || 'leetcode',
          estimated_minutes: initial.estimated_minutes || 20,
          statement_md: initial.statement_md || '',
          constraints_md: initial.constraints_md || '',
          starter_code_md: initial.starter_code_md || '',
          is_active: initial.is_active,
          skill_ids: initial.skill_ids || [],
        }
      : {
          slug: '',
          title: '',
          difficulty: 'easy',
          source: 'leetcode',
          estimated_minutes: 20,
          statement_md: '',
          constraints_md: '',
          starter_code_md: '',
          is_active: true,
          skill_ids: [],
        },
  );
  const [busy, setBusy] = useState(false);

  // We need to lazy-load full editable problem fields from the detail endpoint when
  // editing, but admin list already has slug/title/difficulty/skills. For simplicity
  // we let the admin edit those fields and re-enter the rest if changing.
  // (Future improvement: a GET /api/admin/problems/:id that returns full record.)

  const toggleSkill = (id) =>
    setForm((f) => {
      const has = f.skill_ids.includes(id);
      return { ...f, skill_ids: has ? f.skill_ids.filter((x) => x !== id) : [...f.skill_ids, id] };
    });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    await onSave(form);
    setBusy(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold text-gray-800 mb-4">
          {initial ? `Edit problem #${initial.problem_id}` : 'New problem'}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Title">
              <input
                required
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </Field>
            <Field label="Slug (unique)">
              <input
                required
                value={form.slug}
                onChange={(e) => setForm({ ...form, slug: e.target.value })}
                placeholder="two-sum"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </Field>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Field label="Difficulty">
              <select
                value={form.difficulty}
                onChange={(e) => setForm({ ...form, difficulty: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </Field>
            <Field label="Source">
              <input
                value={form.source || ''}
                onChange={(e) => setForm({ ...form, source: e.target.value })}
                placeholder="leetcode"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </Field>
            <Field label="Est. minutes">
              <input
                type="number"
                min={1}
                value={form.estimated_minutes || ''}
                onChange={(e) => setForm({ ...form, estimated_minutes: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </Field>
          </div>

          <Field label="Statement">
            <textarea
              required
              rows={5}
              value={form.statement_md}
              onChange={(e) => setForm({ ...form, statement_md: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm"
            />
          </Field>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Constraints">
              <textarea
                rows={3}
                value={form.constraints_md || ''}
                onChange={(e) => setForm({ ...form, constraints_md: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-xs"
              />
            </Field>
            <Field label="Starter code">
              <textarea
                rows={3}
                value={form.starter_code_md || ''}
                onChange={(e) => setForm({ ...form, starter_code_md: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-xs"
              />
            </Field>
          </div>

          <Field label="Skills">
            <div className="flex flex-wrap gap-2">
              {skills.map((s) => {
                const active = form.skill_ids.includes(s.skill_id);
                return (
                  <button
                    type="button"
                    key={s.skill_id}
                    onClick={() => toggleSkill(s.skill_id)}
                    className={`text-xs px-3 py-1 rounded-full transition border ${
                      active
                        ? 'bg-indigo-600 text-white border-indigo-600'
                        : 'bg-white text-gray-700 border-gray-300 hover:border-indigo-400'
                    }`}
                  >
                    {s.name}
                  </button>
                );
              })}
            </div>
          </Field>

          <label className="flex items-center text-sm text-gray-700">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
              className="mr-2"
            />
            Active (visible to learners)
          </label>

          <div className="flex justify-end space-x-3 pt-2">
            <button type="button" onClick={onCancel} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
              Cancel
            </button>
            <button type="submit" disabled={busy} className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-60">
              {busy ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
    </div>
  );
}

function capitalize(s) {
  return s ? s[0].toUpperCase() + s.slice(1) : s;
}
