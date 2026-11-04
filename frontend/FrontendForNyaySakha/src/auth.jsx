import { useCallback, useMemo, useState } from 'react'
import { ApiError, api } from './api'
import { AuthContext } from './auth-context'

const TOKEN_KEY = 'nyaysakha_token'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))
  const userId = useMemo(() => readUserId(token), [token])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
  }, [])

  const saveToken = useCallback((next) => {
    localStorage.setItem(TOKEN_KEY, next)
    setToken(next)
  }, [])

  const request = useCallback(async (path, options = {}) => {
    try {
      return await api(path, { ...options, token })
    } catch (error) {
      if (
        token &&
        error instanceof ApiError &&
        (error.status === 401 || error.status === 403)
      ) {
        logout()
      }
      throw error
    }
  }, [logout, token])

  const value = useMemo(
    () => ({ token, userId, saveToken, logout, request }),
    [token, userId, saveToken, logout, request],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

function readUserId(token) {
  if (!token) return null

  try {
    const segment = token.split('.')[1]
    const json = JSON.parse(
      atob(segment.replace(/-/g, '+').replace(/_/g, '/')),
    )
    return json.user_id ? String(json.user_id) : null
  } catch {
    return null
  }
}
