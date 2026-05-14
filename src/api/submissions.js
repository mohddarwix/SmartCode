import { api } from './client';

export const submissionsApi = {
  create: ({ problem_id, code, language = 'python' }) =>
    api.post('/api/submissions', { problem_id, code, language }),
  get: (submissionId) => api.get(`/api/submissions/${submissionId}`),
};
