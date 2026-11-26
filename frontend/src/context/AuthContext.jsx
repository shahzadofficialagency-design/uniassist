import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('user')) } catch { return null }
  })
  const [loading, setLoading] = useState(!!localStorage.getItem('access_token'))

  const fetchMe = useCallback(async () => {
    if (!localStorage.getItem('access_token')) { setLoading(false); return }
    try {
      const { data } = await api.get('/auth/me')
      setUser(data)
      localStorage.setItem('user', JSON.stringify(data))
    } catch {
      setUser(null)
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { fetchMe() }, [fetchMe])

  const login = async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password })
    if (data.access_token) localStorage.setItem('access_token', data.access_token)
    if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
    if (data.user) { setUser(data.user); localStorage.setItem('user', JSON.stringify(data.user)) }
    else await fetchMe()
    return data
  }

  const register = async (payload) => {
    const { data } = await api.post('/auth/register', payload)
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token)
      if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
      if (data.user) { setUser(data.user); localStorage.setItem('user', JSON.stringify(data.user)) }
    }
    return data
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    setUser(null)
  }

  const isAdmin = user?.role === 'admin'

  return (
    <AuthContext.Provider value={{ user, setUser, loading, login, register, logout, isAdmin, fetchMe }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
