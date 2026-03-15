// mar15 API client for GitMax backend endpoints
const BASE = import.meta.env.DEV ? 'http://localhost:8000' : '';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  return res.json();
}

export const api = {
  // Health & config
  health: () => request('/api/health'),
  config: () => request('/api/config'),

  // Setup
  saveAuth: (data) => request('/api/setup/auth', { method: 'POST', body: JSON.stringify(data) }),
  saveLLM: (data) => request('/api/setup/llm', { method: 'POST', body: JSON.stringify(data) }),
  saveSlack: (data) => request('/api/setup/slack', { method: 'POST', body: JSON.stringify(data) }),

  // Tests
  testGithub: () => request('/api/test/github', { method: 'POST' }),
  testLLM: () => request('/api/test/llm', { method: 'POST' }),
  testSlack: () => request('/api/test/slack', { method: 'POST' }),

  // Activity
  activity: () => request('/api/activity'),
};
