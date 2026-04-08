import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor — attach JWT token
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Response interceptor — handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem('access_token', data.access_token);
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          return api(originalRequest);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/en/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  initiateAadhaar: (aadhaar: string) =>
    api.post('/auth/aadhaar/initiate', { aadhaar_number: aadhaar }),
  verifyAadhaar: (txnId: string, otp: string) =>
    api.post('/auth/aadhaar/verify', { txn_id: txnId, otp }),
  refresh: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
  logout: () => api.post('/auth/logout'),
};

// Policies API
export const policiesApi = {
  list: () => api.get('/policies'),
  get: (id: string) => api.get(`/policies/${id}`),
  create: (data: any) => api.post('/policies', data),
  delete: (id: string) => api.delete(`/policies/${id}`),
  checkPmjay: () => api.post('/policies/pmjay/check'),
  checkEligibility: (data: any) => api.post('/policies/eligibility/check', data),
};

// Hospitals API
export const hospitalsApi = {
  list: (params?: any) => api.get('/hospitals', { params }),
  get: (id: string) => api.get(`/hospitals/${id}`),
  getCoverage: (id: string, policyId?: string) =>
    api.get(`/hospitals/${id}/coverage`, { params: { policy_id: policyId } }),
};

// Claims API
export const claimsApi = {
  list: (params?: any) => api.get('/claims', { params }),
  get: (id: string) => api.get(`/claims/${id}`),
  preAuth: (data: any) => api.post('/claims/pre-auth', data),
  reimbursement: (data: any) => api.post('/claims/reimbursement', data),
  uploadDoc: (claimId: string, file: File, docType: string) => {
    const form = new FormData();
    form.append('file', file);
    form.append('doc_type', docType);
    return api.post(`/claims/${claimId}/documents/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  parseOcr: (claimId: string) => api.post(`/claims/${claimId}/ocr/parse`),
  buildFhir: (claimId: string) => api.post(`/claims/${claimId}/fhir/build`),
  gapCheck: (claimId: string) => api.get(`/claims/${claimId}/gap-check`),
  submit: (claimId: string, data: any) => api.post(`/claims/${claimId}/submit`, data),
};

// AI API
export const aiApi = {
  chat: (message: string, history: any[]) =>
    api.post('/ai/eligibility/chat', { message, history }),
  summarizeCoverage: (grid: any, language: string) =>
    api.post('/ai/coverage/summarize', { coverage_grid: grid, language }),
  explainRejection: (code: string, claimId: string, language: string) =>
    api.post('/ai/rejection/explain', { rejection_code: code, claim_id: claimId, language }),
};

// Caregiver API
export const caregiverApi = {
  invite: (phone: string) => api.post('/caregiver/invite', { caregiver_phone: phone }),
  myElders: () => api.get('/caregiver/my-elders'),
  elderDashboard: (elderId: string) => api.get(`/caregiver/elders/${elderId}/dashboard`),
};

// Bank API
export const bankApi = {
  list: () => api.get('/bank-accounts'),
  add: (data: any) => api.post('/bank-accounts', data),
  delete: (id: string) => api.delete(`/bank-accounts/${id}`),
};
