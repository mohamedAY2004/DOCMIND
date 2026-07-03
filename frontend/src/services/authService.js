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

  // No response object → the request never reached (or never heard back from)
  // the server: backend down, connection refused, DNS/CORS, or a timeout.
  // These must NOT be reported as a credential error.
  if (!err?.response) {
    if (err?.code === 'ECONNABORTED' || /timeout/i.test(err?.message ?? '')) {
      return 'The server took too long to respond. Please try again.'
    }
    return 'Cannot reach the server. Please check your connection and try again.'
  }

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

    // Reserve the credential message for an actual 401; other statuses fall
    // back to a neutral message so a 5xx isn't mislabeled as bad credentials.
    const fallback =
      status === 401
        ? 'Invalid username or password.'
        : 'Something went wrong while signing in. Please try again.'
    throw new Error(extractServerMessage(err, fallback))
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
