import axios from 'axios'

// Local dev: '/api' (Vite proxy -> localhost:8000). Production split hosting
// (Netlify + Render): set VITE_API_BASE_URL to the backend URL, e.g.
// https://uniassist-backend.onrender.com/api  (see docs/DEPLOY_SIMPLE_STEPS.md)
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshing = null

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        original._retry = true
        try {
          if (!refreshing) {
            refreshing = axios.post(`${API_BASE}/auth/refresh`, { refresh_token: refresh })
          }
          const { data } = await refreshing
          refreshing = null
          if (data.access_token) localStorage.setItem('access_token', data.access_token)
          if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch {
          refreshing = null
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
        }
      }
    }
    return Promise.reject(error)
  }
)

export function formatPKR(value) {
  if (value === null || value === undefined || value === '') return '—'
  const n = Number(value)
  if (Number.isNaN(n)) return String(value)
  return `Rs ${n.toLocaleString('en-PK')}`
}

export function errorMessage(err, fallback = 'Something went wrong. Please try again.') {
  return err?.response?.data?.detail || err?.response?.data?.message || err?.message || fallback
}

export default api
