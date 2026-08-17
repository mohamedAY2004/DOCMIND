import apiClient from './apiClient'

export async function getReadiness(subjectId) {
  return (await apiClient.get(`/subjects/${subjectId}/readiness`)).data
}
export async function listEvaluationCases(subjectId) {
  return (await apiClient.get(`/subjects/${subjectId}/evaluation-cases`)).data
}
export async function createEvaluationCase(subjectId, body) {
  return (await apiClient.post(`/subjects/${subjectId}/evaluation-cases`, body)).data
}
export async function deleteEvaluationCase(subjectId, caseId) {
  await apiClient.delete(`/subjects/${subjectId}/evaluation-cases/${caseId}`)
}
export async function listEvaluationRuns(subjectId) {
  return (await apiClient.get(`/subjects/${subjectId}/evaluation-runs`)).data
}
export async function startEvaluationRun(subjectId) {
  return (await apiClient.post(`/subjects/${subjectId}/evaluation-runs`)).data
}
export async function getEvaluationResults(subjectId, runId) {
  return (await apiClient.get(`/subjects/${subjectId}/evaluation-runs/${runId}/results`)).data
}
export async function listAllEvaluationRuns() {
  return (await apiClient.get('/admin/evaluations/runs')).data
}
export async function listTutorFeedback(subjectId) {
  return (await apiClient.get(`/subjects/${subjectId}/feedback`, { params: { pageSize: 50 } })).data
}
export async function convertFeedbackToCase(subjectId, feedbackId, body) {
  return (await apiClient.post(`/subjects/${subjectId}/feedback/${feedbackId}/evaluation-case`, body)).data
}
