import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';

import LoginScreen from './screens/auth/LoginScreen';
import RegisterScreen from './screens/auth/RegisterScreen';

import DiagnosticScreen from './screens/student/DiagnosticScreen';
import DashboardScreen from './screens/student/DashboardScreen';
import ProblemListScreen from './screens/student/ProblemListScreen';
import EditorScreen from './screens/student/EditorScreen';
import FeedbackScreen from './screens/student/FeedbackScreen';

import AdminDashboardScreen from './screens/admin/AdminDashboardScreen';
import AdminProblemsScreen from './screens/admin/AdminProblemsScreen';
import AdminSkillsScreen from './screens/admin/AdminSkillsScreen';
import AdminAssessmentsScreen from './screens/admin/AdminAssessmentsScreen';
import AdminUsersScreen from './screens/admin/AdminUsersScreen';

function RootRedirect() {
  const { user, loading, hasCompletedDiagnostic } = useAuth();
  if (loading) return <FullScreenSpinner />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === 'admin') return <Navigate to="/admin" replace />;
  if (!hasCompletedDiagnostic) return <Navigate to="/diagnostic" replace />;
  return <Navigate to="/dashboard" replace />;
}

// Gate every student route except /diagnostic itself: if the user hasn't
// completed their initial assessment yet, send them there. Beta testers found
// they could click `/dashboard` or `/problems` from the URL bar and bypass it.
function DiagnosticGate({ children }) {
  const { user, loading, hasCompletedDiagnostic } = useAuth();
  const location = useLocation();
  if (loading) return <FullScreenSpinner />;
  // Admins are exempt (they don't take the diagnostic). Anyone not logged in
  // hits ProtectedRoute's redirect; this guard runs after that.
  if (user?.role !== 'student') return children;
  if (hasCompletedDiagnostic) return children;
  if (location.pathname === '/diagnostic') return children;
  return <Navigate to="/diagnostic" replace />;
}

function FullScreenSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<RootRedirect />} />
          <Route path="/login" element={<LoginScreen />} />
          <Route path="/register" element={<RegisterScreen />} />

          <Route
            element={
              <ProtectedRoute requireRole="student">
                <DiagnosticGate>
                  <Layout />
                </DiagnosticGate>
              </ProtectedRoute>
            }
          >
            <Route path="/diagnostic" element={<DiagnosticScreen />} />
            <Route path="/dashboard" element={<DashboardScreen />} />
            <Route path="/problems" element={<ProblemListScreen />} />
            <Route path="/problems/:id" element={<EditorScreen />} />
            <Route path="/feedback/:submissionId" element={<FeedbackScreen />} />
          </Route>

          <Route
            element={
              <ProtectedRoute requireRole="admin">
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/admin" element={<AdminDashboardScreen />} />
            <Route path="/admin/problems" element={<AdminProblemsScreen />} />
            <Route path="/admin/skills" element={<AdminSkillsScreen />} />
            <Route path="/admin/assessments" element={<AdminAssessmentsScreen />} />
            <Route path="/admin/users" element={<AdminUsersScreen />} />
          </Route>

          <Route path="*" element={<RootRedirect />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
