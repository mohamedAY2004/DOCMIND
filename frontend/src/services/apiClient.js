import axios from 'axios'
import { STUDENT_ACCESS_DISABLED } from '../constants/studentAccess'
import { goToStudentUnavailable } from '../utils/studentAccessNavigation'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
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
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export default apiClient
