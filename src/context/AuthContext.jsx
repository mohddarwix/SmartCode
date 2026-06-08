import { createContext, useContext, useEffect, useState } from 'react';
import { ApiError, getToken, setToken } from '../api/client';
import { authApi } from '../api/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Validate any stored token by calling /me on mount.
  useEffect(() => {
    let cancelled = false;
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then((u) => !cancelled && setUser(u))
      .catch(() => {
        setToken(null);
        if (!cancelled) setUser(null);
      })
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  const login = async ({ email, password }) => {
    const data = await authApi.login({ email, password });
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  };

  const register = async ({ name, email, password, confirmPassword }) => {
    if (!name || !email || !password) {
      throw new Error('All fields are required.');
    }
    if (password !== confirmPassword) {
      throw new Error('Passwords do not match.');
    }
    try {
      const data = await authApi.register({ full_name: name, email, password });
      setToken(data.access_token);
      setUser(data.user);
      return data.user;
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new Error(err?.message || 'Registration failed.', { cause: err });
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    const u = await authApi.me();
    setUser(u);
    return u;
  };

  const hasCompletedDiagnostic = !!user?.diagnostic_completed_at;

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        refreshUser,
        setUser,
        hasCompletedDiagnostic,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside an AuthProvider');
  return ctx;
}
