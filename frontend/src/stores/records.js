import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { recordsApi } from '../api/billing'

export const useRecordsStore = defineStore('records', () => {
  const items = ref([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref(null)

  const filters = reactive({
    provider: '',
    account_id: '',
    period: '',
    expense_category: '',
    financial_basis: '',
    ownership_type: 'geidi',
    validation_status: '',
    page: 1,
    page_size: 50,
  })

  async function fetchRecords() {
    loading.value = true
    error.value = null
    try {
      const params = Object.fromEntries(
        Object.entries(filters).filter(([, v]) => v !== '' && v !== null)
      )
      const res = await recordsApi.list(params)
      items.value = res.data.items
      total.value = res.data.total
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load records'
    } finally {
      loading.value = false
    }
  }

  function setFilter(key, value) {
    filters[key] = value
    filters.page = 1
  }

  function nextPage() { filters.page++ }
  function prevPage() { if (filters.page > 1) filters.page-- }

  return { items, total, loading, error, filters, fetchRecords, setFilter, nextPage, prevPage }
})
