/** Registered from inside <Router> so apiClient can navigate without importing React. */
let navigateRef = null

/** @param {import('react-router-dom').NavigateFunction | null} navigate */
export function registerStudentAccessNavigation(navigate) {
  navigateRef = navigate
}

export function goToStudentUnavailable() {
  if (navigateRef) {
    navigateRef('/student-unavailable', { replace: true })
  } else {
    window.location.assign('/student-unavailable')
  }
}
