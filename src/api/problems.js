import { api, streamSSE } from './client';

export const problemsApi = {
  list:         ()                          => api.get('/api/problems'),
  detail:       (problemId)                 => api.get(`/api/problems/${problemId}`),
  hintPreview:  (problemId)                 => api.get(`/api/problems/${problemId}/hint/preview`),
  hint:         (problemId, { code = '', language = 'python', level = 1 } = {}) =>
                  api.post(`/api/problems/${problemId}/hint`, { code, language, level }),
  aiSolution:   (problemId)                 => api.get(`/api/problems/${problemId}/ai-solution`),
  // Stream the AI solving the problem live. `onChunk` is called with {text} or {error}.
  // Returns a Promise that resolves when the stream completes.
  streamAiSolve: (problemId, onChunk, signal) =>
                  streamSSE(`/api/problems/${problemId}/ai-solve/stream`, { method: 'POST', signal }, onChunk),
  // Interactive step-by-step tutor: one turn at a time. `history` is the full
  // conversation so far (the backend is stateless); `studentMessage` is null
  // on the very first call.
  tutorTurn:    (problemId, { history = [], studentMessage = null } = {}) =>
                  api.post(`/api/problems/${problemId}/ai-tutor/turn`, {
                    history,
                    student_message: studentMessage,
                  }),
  // Read-only review of the user's accepted submission once a problem is solved.
  myAttempt:    (problemId)                 => api.get(`/api/problems/${problemId}/my-attempt`),
  // List of all the user's Submit attempts on this problem (newest first).
  mySubmissions:(problemId)                 => api.get(`/api/problems/${problemId}/my-submissions`),
  // Plain Run: sandbox only, no LLM, fast smoke test (LeetCode-style "Run Code").
  run:          (problemId, { code, language = 'python' }) =>
                  api.post(`/api/problems/${problemId}/run`, { code, language }),
  // AI Run: sandbox + LLM commentary (severity, explanations). Slower, costs tokens.
  runWithAi:    (problemId, { code, language = 'python' }) =>
                  api.post(`/api/problems/${problemId}/run-ai`, { code, language }),
};
