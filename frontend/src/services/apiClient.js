import axios from 'axios'
import { STUDENT_ACCESS_DISABLED } from '../constants/studentAccess'
import { goToStudentUnavailable } from '../utils/studentAccessNavigation'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

/**
 * Default timeout for normal JSON requests (30 s).
 * Upload and LLM-generation calls override this per-request.
 */
const DEFAULT_TIMEOUT = 30_000

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: DEFAULT_TIMEOUT,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
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
      // Do not hard-redirect on failed login — that reloads the page and hides
      // inline error messages. Other 401s mean an expired/invalid session.
      const url = String(error.config?.url ?? '')
      const isLoginAttempt = /\/auth\/login\/?$/.test(url) || url.endsWith('auth/login')
      if (!isLoginAttempt) {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('auth_user')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

/**
 * Timeout presets for specific operation types. Import from here and spread
 * into your axios config when calling long-running endpoints.
 */
export const UPLOAD_TIMEOUT = { timeout: 5 * 60_000 } // 5 minutes — large PDFs
export const LLM_TIMEOUT = { timeout: 6 * 60_000 }    // 6 minutes — LLM generation + reranking can be slow

export default apiClient
