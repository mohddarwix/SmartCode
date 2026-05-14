import { Link, NavLink, useNavigate } from 'react-router-dom';
import { Code, User, LogOut, Shield } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Nav() {
  const { user, logout, hasCompletedDiagnostic } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isAdmin = user?.role === 'admin';
  // Students who haven't completed the diagnostic shouldn't see nav tabs to
  // pages the DiagnosticGate would just bounce them back from.
  const showStudentTabs = user && !isAdmin && hasCompletedDiagnostic;

  return (
    <nav className="bg-white shadow-sm border-b sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <Link to={user ? (isAdmin ? '/admin' : '/dashboard') : '/login'} className="flex items-center space-x-2">
          <Code className="w-8 h-8 text-indigo-600" />
          <span className="text-xl font-bold text-gray-800">SmartCode</span>
        </Link>

        {showStudentTabs && (
          <div className="hidden md:flex items-center space-x-1">
            <NavTab to="/dashboard" label="Dashboard" />
            <NavTab to="/problems" label="Problems" />
          </div>
        )}
        {user && !isAdmin && !hasCompletedDiagnostic && (
          <div className="hidden md:flex items-center">
            <span className="text-xs font-medium uppercase tracking-wide bg-amber-100 text-amber-800 px-2 py-1 rounded">
              Complete the diagnostic to unlock
            </span>
          </div>
        )}

        {user && isAdmin && (
          <div className="hidden md:flex items-center space-x-1">
            <NavTab to="/admin" label="Overview" end />
            <NavTab to="/admin/problems" label="Problems" />
            <NavTab to="/admin/skills" label="Skills" />
            <NavTab to="/admin/assessments" label="Assessments" />
            <NavTab to="/admin/users" label="Users" />
          </div>
        )}

        <div className="flex items-center space-x-3">
          {user ? (
            <>
              <span className="hidden sm:inline-flex items-center text-sm text-gray-600">
                {isAdmin && <Shield className="w-4 h-4 mr-1 text-indigo-600" />}
                {user.full_name}
              </span>
              <User className="w-6 h-6 text-gray-600" />
              <button
                onClick={handleLogout}
                className="text-gray-600 hover:text-red-600 transition flex items-center space-x-1"
                title="Sign out"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </>
          ) : (
            <Link to="/login" className="text-indigo-600 hover:underline text-sm font-medium">
              Sign in
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}

function NavTab({ to, label, end }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `px-4 py-2 rounded-lg text-sm font-medium transition ${
          isActive ? 'bg-indigo-50 text-indigo-700' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
        }`
      }
    >
      {label}
    </NavLink>
  );
}
