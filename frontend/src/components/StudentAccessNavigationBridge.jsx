import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { registerStudentAccessNavigation } from '../utils/studentAccessNavigation'

function StudentAccessNavigationBridge() {
  const navigate = useNavigate()
  useEffect(() => {
    registerStudentAccessNavigation(navigate)
    return () => registerStudentAccessNavigation(null)
  }, [navigate])
  return null
}

export default StudentAccessNavigationBridge
