import axios from 'axios'
import { STUDENT_ACCESS_DISABLED } from '../constants/studentAccess'
import { goToStudentUnavailable } from '../utils/studentAccessNavigation'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

let refreshPromise = null

export function refreshBrowserSession() {
  if (!refreshPromise) {
    refreshPromise = apiClient.post('/auth/refresh')
      .catch((error) => {
        window.dispatchEvent(new Event('docmind:session-expired'))
        throw error
      })
      .finally(() => { refreshPromise = null })
  }
  return refreshPromise
}

apiClient.interceptors.request.use((config) => {
  const method = String(config.method || 'get').toUpperCase()
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const csrf = readCookie('docmind_csrf')
    if (csrf) config.headers['X-CSRF-Token'] = csrf
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    if (status === 403 && error.response?.data?.code === STUDENT_ACCESS_DISABLED) {
      goToStudentUnavailable()
      return Promise.reject(error)
    }
    if (status === 401) {
      const original = error.config || {}
      const url = String(original.url ?? '')
      const isAuthAttempt = /\/auth\/(login|refresh|sso\/exchange)\/?$/.test(url)
      if (!isAuthAttempt && !original._sessionRetry) {
        original._sessionRetry = true
        return refreshBrowserSession().then(() => apiClient(original))
      }
    }
    return Promise.reject(error)
  },
)

export const UPLOAD_TIMEOUT = { timeout: 5 * 60_000 }
export const LLM_TIMEOUT = { timeout: 6 * 60_000 }

export function readCookie(name) {
  const prefix = `${encodeURIComponent(name)}=`
  const part = document.cookie.split('; ').find((value) => value.startsWith(prefix))
  return part ? decodeURIComponent(part.slice(prefix.length)) : ''
}

export default apiClient
