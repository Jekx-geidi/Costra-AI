import axios from 'axios'

const client = axios.create({
  // Route dev traffic through Vite so shared ports work on other devices.
  baseURL: import.meta.env.DEV ? '/api' : (import.meta.env.VITE_API_BASE_URL || '/api'),
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (res) => res,
  async (err) => {
    // A 401 from the login call means wrong credentials: let the form show the error instead of reloading.
    if (err.response?.status === 401 && err.config?.url !== '/auth/login') {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export default client
