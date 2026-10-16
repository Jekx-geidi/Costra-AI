import client from './client'

export const authApi = {
  login: (email, password) => client.post('/auth/login', { email, password }),
  me: () => client.get('/auth/me'),
}

export const accountsApi = {
  list: () => client.get('/ai-billing/accounts'),
  create: (data) => client.post('/ai-billing/accounts', data),
  update: (id, data) => client.patch(`/ai-billing/accounts/${id}`, data),
}

export const importsApi = {
  upload: (formData) => client.post('/ai-billing/imports', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  get: (id) => client.get(`/ai-billing/imports/${id}`),
  list: () => client.get('/ai-billing/imports'),
}

export const recordsApi = {
  list: (params) => client.get('/ai-billing/records', { params }),
}

export const syncApi = {
  trigger: (provider, data) => client.post(`/ai-billing/sync/${provider}`, data),
}

export const reconciliationApi = {
  list: (params) => client.get('/ai-billing/reconciliation', { params }),
  create: (data) => client.post('/ai-billing/reconciliation', data),
  review: (billingRecordId, data) => client.post(`/ai-billing/reconciliation/${billingRecordId}/review`, data),
}

export const assistantApi = {
  chat: (messages) => client.post('/assistant/chat', { messages }),
  readInvoice: (formData) => client.post('/assistant/invoice', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  confirmInvoice: (draftId, data) => client.post(`/assistant/invoice/${draftId}/confirm`, data),
}

export const reportingApi = {
  summary: (period) => client.get('/ai-billing/summary', { params: { period } }),
  trends: (months = 12) => client.get('/ai-billing/trends', { params: { months } }),
}
