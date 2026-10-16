import { defineStore } from 'pinia'
import { ref } from 'vue'
import { reportingApi } from '../api/billing'

function currentPeriod() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

export const useReportingStore = defineStore('reporting', () => {
  const summary = ref(null)
  const trends = ref([])
  const selectedPeriod = ref(currentPeriod())
  const loadingSummary = ref(false)
  const loadingTrends = ref(false)
  const error = ref(null)

  async function fetchSummary(period) {
    if (period) selectedPeriod.value = period
    loadingSummary.value = true
    error.value = null
    try {
      const res = await reportingApi.summary(selectedPeriod.value)
      summary.value = res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load summary'
    } finally {
      loadingSummary.value = false
    }
  }

  async function fetchTrends(months = 12) {
    loadingTrends.value = true
    try {
      const res = await reportingApi.trends(months)
      trends.value = res.data.months
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load trends'
    } finally {
      loadingTrends.value = false
    }
  }

  return {
    summary, trends, selectedPeriod, loadingSummary, loadingTrends, error,
    fetchSummary, fetchTrends,
  }
})
