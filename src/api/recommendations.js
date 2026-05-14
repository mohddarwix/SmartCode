import { api } from './client';

export const recommendationsApi = {
  next: () => api.get('/api/me/recommendations/next'),
};
