import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/billing'

function decodeJwt(token) {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(base64))
  } catch {
    return {}
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || null)
  const user = ref(null)

  const isAuthenticated = computed(() => !!token.value)
  const role = computed(() => {
    if (!token.value) return null
    return decodeJwt(token.value).role || null
  })

  async function login(email, password) {
    const res = await authApi.login(email, password)
    token.value = res.data.access_token
    localStorage.setItem('access_token', token.value)
    await fetchMe()
  }

  async function fetchMe() {
    if (!token.value) return
    const res = await authApi.me()
    user.value = res.data
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('access_token')
  }

  function canAccess(minRole) {
    const levels = { viewer: 0, finance_reviewer: 1, billing_admin: 2 }
    return (levels[role.value] ?? -1) >= (levels[minRole] ?? 0)
  }

  return { token, user, isAuthenticated, role, login, fetchMe, logout, canAccess }
})
