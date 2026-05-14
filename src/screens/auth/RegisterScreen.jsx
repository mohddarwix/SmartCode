import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Code, Check, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

// Mirror of backend/app/schemas.py::_validate_strong_password so the UI can
// give live feedback before the user submits. Keep these in sync.
function passwordChecks(pwd) {
  const trimmed = pwd ?? '';
  return [
    { label: 'At least 8 characters',     ok: trimmed.length >= 8 },
    { label: 'One lowercase letter (a-z)', ok: /[a-z]/.test(trimmed) },
    { label: 'One uppercase letter (A-Z)', ok: /[A-Z]/.test(trimmed) },
    { label: 'One digit (0-9)',            ok: /\d/.test(trimmed) },
  ];
}

export default function RegisterScreen() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '' });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showPasswordHelp, setShowPasswordHelp] = useState(false);

  const update = (field) => (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const checks = useMemo(() => passwordChecks(form.password), [form.password]);
  const allChecksPass = checks.every((c) => c.ok);
  const passwordsMatch =
    form.password.length > 0 && form.confirmPassword.length > 0 && form.password === form.confirmPassword;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    // Client-side guard before hitting the server.
    if (!allChecksPass) {
      setError('Password does not meet all requirements.');
      setShowPasswordHelp(true);
      return;
    }
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setSubmitting(true);
    try {
      await register(form);
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message || 'Registration failed.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-full mb-4">
            <Code className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-800">Create your account</h1>
          <p className="text-gray-600 mt-2">Start your personalized learning journey</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Field label="Full name" type="text" autoComplete="name" value={form.name} onChange={update('name')} placeholder="Ada Lovelace" required />
          <Field label="Email" type="email" autoComplete="email" value={form.email} onChange={update('email')} placeholder="your@email.com" required />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              autoComplete="new-password"
              value={form.password}
              onChange={update('password')}
              onFocus={() => setShowPasswordHelp(true)}
              placeholder="Min 8 chars, mixed case, a digit"
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            {(showPasswordHelp || form.password.length > 0) && (
              <ul className="mt-2 text-xs space-y-1">
                {checks.map((c) => (
                  <li
                    key={c.label}
                    className={`flex items-center gap-1.5 ${c.ok ? 'text-green-700' : 'text-gray-500'}`}
                  >
                    {c.ok ? (
                      <Check className="w-3.5 h-3.5 flex-shrink-0" />
                    ) : (
                      <X className="w-3.5 h-3.5 flex-shrink-0" />
                    )}
                    {c.label}
                  </li>
                ))}
                <li className="text-[11px] text-gray-400 mt-1 italic">
                  Common passwords (e.g. password123, qwerty123) are blocked.
                </li>
              </ul>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Confirm password</label>
            <input
              type="password"
              autoComplete="new-password"
              value={form.confirmPassword}
              onChange={update('confirmPassword')}
              placeholder="Repeat your password"
              required
              className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent ${
                form.confirmPassword.length > 0 && !passwordsMatch
                  ? 'border-red-400'
                  : 'border-gray-300'
              }`}
            />
            {form.confirmPassword.length > 0 && !passwordsMatch && (
              <p className="text-xs text-red-600 mt-1">Passwords don't match.</p>
            )}
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">{error}</div>
          )}

          <button
            type="submit"
            disabled={submitting || !allChecksPass || !passwordsMatch}
            className="w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold hover:bg-indigo-700 transition disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {submitting ? 'Creating account...' : 'Create account'}
          </button>

          <p className="text-center text-sm text-gray-600">
            Already have an account?{' '}
            <Link to="/login" className="text-indigo-600 font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}

function Field({ label, ...props }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      <input
        {...props}
        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
      />
    </div>
  );
}
