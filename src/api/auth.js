import { api } from './client';

export const authApi = {
  login: ({ email, password }) =>
    api.post('/api/auth/login', { email, password }, { auth: false }),

  register: ({ full_name, email, password }) =>
    api.post('/api/auth/register', { full_name, email, password }, { auth: false }),

  me: () => api.get('/api/auth/me'),
};
