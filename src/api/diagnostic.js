import { api } from './client';

export const diagnosticApi = {
  // POST /api/diagnostic — body: { items: [...] }
  // items[i] = { order_index, skill_name, type ('mcq'|'coding'), question,
  //              user_answer, correct_answer (mcq only), time_spent_seconds, hints_used }
  submit: (items) => api.post('/api/diagnostic', { items }),

  // GET /api/diagnostic/last — most recent completed diagnostic for the current user
  last: () => api.get('/api/diagnostic/last'),
};
