import { api } from './client';

export const skillsApi = {
  mySkills:        ()           => api.get('/api/me/skills'),
  mySkillHistory:  (skillId)    => api.get(`/api/me/skills/history?skill_id=${skillId}`),
  catalog:         ()           => api.get('/api/skills'),
};
