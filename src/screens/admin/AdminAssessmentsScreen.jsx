import { useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { diagnosticQuestions } from '../../data/mock';

const initialAssessments = [
  {
    id: 1,
    name: 'Default Diagnostic',
    description: '6 MCQs + 2 coding problems, covers all six core skills.',
    active: true,
    questionCount: diagnosticQuestions.length,
  },
  {
    id: 2,
    name: 'Quick Refresher',
    description: '4 MCQs for users returning after a break.',
    active: false,
    questionCount: 4,
  },
];

export default function AdminAssessmentsScreen() {
  const [assessments, setAssessments] = useState(initialAssessments);
  const [showForm, setShowForm] = useState(false);

  const handleCreate = (data) => {
    setAssessments((prev) => [...prev, { id: Date.now(), questionCount: 0, active: true, ...data }]);
    setShowForm(false);
  };

  const toggle = (id) =>
    setAssessments((prev) => prev.map((a) => (a.id === id ? { ...a, active: !a.active } : a)));

  const remove = (id) => {
    if (confirm('Delete this assessment?')) setAssessments((prev) => prev.filter((a) => a.id !== id));
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Assessments</h1>
          <p className="text-gray-600 text-sm">Manage diagnostic tests used to evaluate user skill levels.</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 transition flex items-center"
        >
          <Plus className="w-4 h-4 mr-1" /> New assessment
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {assessments.map((a) => (
          <div key={a.id} className="bg-white rounded-xl shadow-md p-5">
            <div className="flex items-start justify-between mb-2">
              <h3 className="font-bold text-gray-800">{a.name}</h3>
              <button
                onClick={() => remove(a.id)}
                className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded"
                title="Delete"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-4">{a.description}</p>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-700">
                <strong>{a.questionCount}</strong> question{a.questionCount === 1 ? '' : 's'}
              </span>
              <label className="inline-flex items-center cursor-pointer">
                <input type="checkbox" checked={a.active} onChange={() => toggle(a.id)} className="sr-only peer" />
                <span className="w-10 h-5 bg-gray-300 rounded-full peer peer-checked:bg-indigo-600 relative transition">
                  <span
                    className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition ${
                      a.active ? 'translate-x-5' : ''
                    }`}
                  />
                </span>
                <span className="ml-2 text-xs text-gray-600">{a.active ? 'Active' : 'Inactive'}</span>
              </label>
            </div>
          </div>
        ))}
      </div>

      {showForm && <AssessmentForm onCancel={() => setShowForm(false)} onSave={handleCreate} />}
    </div>
  );
}

function AssessmentForm({ onCancel, onSave }) {
  const [form, setForm] = useState({ name: '', description: '' });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(form);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md">
        <h2 className="text-xl font-bold text-gray-800 mb-4">New assessment</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div className="flex justify-end space-x-3 pt-2">
            <button type="button" onClick={onCancel} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
              Cancel
            </button>
            <button type="submit" className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700">
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
