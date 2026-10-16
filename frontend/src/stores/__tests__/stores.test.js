// @vitest-environment happy-dom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('../../api/billing', () => ({
  authApi: { login: vi.fn(), me: vi.fn() },
  reportingApi: { summary: vi.fn(), trends: vi.fn() },
  recordsApi: { list: vi.fn() },
}))

const { authApi, reportingApi, recordsApi } = await import('../../api/billing')
const { useAuthStore } = await import('../auth')
const { useReportingStore } = await import('../reporting')
const { useRecordsStore } = await import('../records')

function fakeJwt(payload) {
  const b64 = s => btoa(JSON.stringify(s)).replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_')
  return `${b64({ alg: 'HS256' })}.${b64(payload)}.signature`
}

beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
  setActivePinia(createPinia())
})

describe('auth store', () => {
  it('login stores the token, decodes the role and loads the user', async () => {
    const token = fakeJwt({ sub: 'finance@geidi.com', role: 'finance_reviewer' })
    authApi.login.mockResolvedValue({ data: { access_token: token } })
    authApi.me.mockResolvedValue({ data: { email: 'finance@geidi.com', role: 'finance_reviewer' } })

    const auth = useAuthStore()
    await auth.login('finance@geidi.com', 'pw')

    expect(authApi.login).toHaveBeenCalledWith('finance@geidi.com', 'pw')
    expect(localStorage.getItem('access_token')).toBe(token)
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.role).toBe('finance_reviewer')
    expect(auth.user.email).toBe('finance@geidi.com')
  })

  it('canAccess follows the role ladder', async () => {
    authApi.login.mockResolvedValue({ data: { access_token: fakeJwt({ role: 'finance_reviewer' }) } })
    authApi.me.mockResolvedValue({ data: {} })
    const auth = useAuthStore()
    await auth.login('x', 'y')
    expect(auth.canAccess('viewer')).toBe(true)
    expect(auth.canAccess('finance_reviewer')).toBe(true)
    expect(auth.canAccess('billing_admin')).toBe(false)
  })

  it('logout clears everything', async () => {
    authApi.login.mockResolvedValue({ data: { access_token: fakeJwt({ role: 'viewer' }) } })
    authApi.me.mockResolvedValue({ data: {} })
    const auth = useAuthStore()
    await auth.login('x', 'y')
    auth.logout()
    expect(auth.isAuthenticated).toBe(false)
    expect(auth.role).toBe(null)
    expect(localStorage.getItem('access_token')).toBe(null)
  })

  it('a failed login leaves the user signed out', async () => {
    authApi.login.mockRejectedValue({ response: { status: 401 } })
    const auth = useAuthStore()
    await expect(auth.login('x', 'bad')).rejects.toBeTruthy()
    expect(auth.isAuthenticated).toBe(false)
  })
})

describe('reporting store', () => {
  it('keeps all 12 months, including unavailable ones, with amounts as strings', async () => {
    const months = Array.from({ length: 12 }, (_, i) => ({
      period: `2026-${String(i + 1).padStart(2, '0')}`,
      actual_expense: i === 8 ? '244.820000' : null,
      coverage_status: i === 8 ? 'partial' : 'unavailable',
      currency: 'USD',
    }))
    reportingApi.trends.mockResolvedValue({ data: { months, currency: 'USD' } })

    const reporting = useReportingStore()
    await reporting.fetchTrends()

    expect(reportingApi.trends).toHaveBeenCalledWith(12)
    expect(reporting.trends).toHaveLength(12)
    expect(reporting.trends.filter(m => m.coverage_status === 'unavailable')).toHaveLength(11)
    expect(reporting.trends[8].actual_expense).toBe('244.820000')
  })

  it('surfaces API errors instead of throwing', async () => {
    reportingApi.summary.mockRejectedValue({ response: { data: { detail: 'boom' } } })
    const reporting = useReportingStore()
    await reporting.fetchSummary('2026-09')
    expect(reporting.error).toBe('boom')
    expect(reporting.selectedPeriod).toBe('2026-09')
  })
})

describe('records store', () => {
  it('sends only the filters that are set, and resets paging on filter change', async () => {
    recordsApi.list.mockResolvedValue({ data: { items: [{ id: '1', amount: '150.000000' }], total: 1 } })
    const records = useRecordsStore()
    records.nextPage()
    records.setFilter('provider', 'openai')
    await records.fetchRecords()

    expect(recordsApi.list).toHaveBeenCalledWith({ ownership_type: 'geidi', provider: 'openai', page: 1, page_size: 50 })
    expect(records.items[0].amount).toBe('150.000000')
    expect(records.total).toBe(1)
  })
})
