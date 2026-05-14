import { api } from './client';

export const adminApi = {
  stats:         ()                      => api.get('/api/admin/stats'),
  users:         ()                      => api.get('/api/admin/users'),
  userDetail:    (userId)                => api.get(`/api/admin/users/${userId}`),

  listProblems:  ()                      => api.get('/api/admin/problems'),
  createProblem: (data)                  => api.post('/api/admin/problems', data),
  updateProblem: (id, data)              => api.put(`/api/admin/problems/${id}`, data),
  deleteProblem: (id)                    => api.delete(`/api/admin/problems/${id}`),

  listSkills:    ()                      => api.get('/api/admin/skills'),
  createSkill:   (data)                  => api.post('/api/admin/skills', data),
  updateSkill:   (id, data)              => api.put(`/api/admin/skills/${id}`, data),
  deleteSkill:   (id)                    => api.delete(`/api/admin/skills/${id}`),

  listTestCases:   (problemId)           => api.get(`/api/admin/problems/${problemId}/test-cases`),
  createTestCase:  (problemId, data)     => api.post(`/api/admin/problems/${problemId}/test-cases`, data),
  updateTestCase:  (tcId, data)          => api.put(`/api/admin/test-cases/${tcId}`, data),
  deleteTestCase:  (tcId)                => api.delete(`/api/admin/test-cases/${tcId}`),

  createUser:    (data)                  => api.post('/api/admin/users', data),
};
