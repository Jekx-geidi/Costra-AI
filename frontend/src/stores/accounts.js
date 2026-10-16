import { defineStore } from 'pinia'
import { ref } from 'vue'
import { accountsApi } from '../api/billing'

export const useAccountsStore = defineStore('accounts', () => {
  const accounts = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchAccounts() {
    loading.value = true
    error.value = null
    try {
      const res = await accountsApi.list()
      accounts.value = res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load accounts'
    } finally {
      loading.value = false
    }
  }

  async function createAccount(data) {
    const res = await accountsApi.create(data)
    accounts.value.unshift(res.data)
    return res.data
  }

  async function updateAccount(id, data) {
    const res = await accountsApi.update(id, data)
    const idx = accounts.value.findIndex((a) => a.id === id)
    if (idx !== -1) accounts.value[idx] = res.data
    return res.data
  }

  return { accounts, loading, error, fetchAccounts, createAccount, updateAccount }
})
