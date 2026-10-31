// Base URL for API calls - change this to your deployed backend URL
export const API_BASE = 'http://localhost:8000';

// Get stored token
export const getToken = () => localStorage.getItem('gg_token');

// Generic authenticated fetch
async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw Object.assign(new Error(err.detail || 'Request failed'), { status: res.status });
  }
  return res.json();
}

// --- Auth ---
export const login = (email, password) =>
  apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });

// --- Consumers ---
export const getRiskQueue = (params = {}) => {
  const q = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v && v !== 'all'))
  ).toString();
  return apiFetch(`/consumers/risk-queue${q ? '?' + q : ''}`);
};

export const getExplanation = (id) => apiFetch(`/consumers/${id}/explanation`);
export const getConsumptionHistory = (id) => apiFetch(`/consumers/${id}/consumption-history`);

// --- Users (inspectors) ---
export const getInspectors = () => apiFetch('/users');

// --- Cases ---
export const createCase = (body) =>
  apiFetch('/cases', { method: 'POST', body: JSON.stringify(body) });

export const getCases = (params = {}) => {
  const q = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v && v !== 'all'))
  ).toString();
  return apiFetch(`/cases${q ? '?' + q : ''}`);
};

export const getCaseDetail = (id) => apiFetch(`/cases/${id}`);
export const getCaseAuditLog = (id) => apiFetch(`/cases/${id}/audit-log`);

// --- Analytics ---
export const getModelPerformance = () => apiFetch('/analytics/model-performance');
