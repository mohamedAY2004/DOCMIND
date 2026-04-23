import apiClient from './apiClient'
import { STUDENT_ACCESS_DISABLED } from '../constants/studentAccess'

/**
 * Auth service.
 *
 * Backend contract (see API_SPECIFICATION.md §4):
 *   POST /auth/login   → 200 { token, user: { id, username, name, role }, redirect, welcomeMessage? }
 *                        403 STUDENT_ACCESS_DISABLED for disabled student logins.
 *   POST /auth/logout  → 204
 */

function extractServerMessage(err, fallback) {
  const data = err?.response?.data
  if (data?.message) return data.message
  return fallback
}

export async function login(username, password) {
  try {
    const { data } = await apiClient.post('/auth/login', { username, password })
    return data
  } catch (err) {
    const status = err?.response?.status
    const code = err?.response?.data?.code

    if (status === 403 && code === STUDENT_ACCESS_DISABLED) {
      const wrapped = new Error(
        extractServerMessage(
          err,
          'Student access is currently disabled. Please try again later.',
        ),
      )
      wrapped.code = STUDENT_ACCESS_DISABLED
      throw wrapped
    }

    throw new Error(extractServerMessage(err, 'Invalid username or password.'))
  }
}

export async function logout() {
  try {
    await apiClient.post('/auth/logout')
  } catch {
    /* swallow — server may have already revoked the token. */
  } finally {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
  }
}
