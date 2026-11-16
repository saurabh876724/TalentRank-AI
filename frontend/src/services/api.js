import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
  timeout: 180000,
})

export function getApiError(error) {
  if (error.response) {
    const detail = error.response.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
    return `Request failed (HTTP ${error.response.status}).`
  }
  if (error.code === 'ECONNABORTED') {
    return 'The request timed out. The backend may still be loading the AI model — please retry.'
  }
  if (error.request) {
    return 'Cannot reach the backend server. Make sure it is running on ' + api.defaults.baseURL
  }
  return error.message || 'Unexpected error.'
}

export const fetchHealth = () => api.get('/health').then((r) => r.data)

export const fetchStats = () => api.get('/api/stats').then((r) => r.data)

export const fetchCandidates = () => api.get('/api/candidates').then((r) => r.data)

export const fetchCandidate = (id) => api.get(`/api/candidates/${id}`).then((r) => r.data)

export const fetchLatestAnalysis = () => api.get('/api/matching/latest').then((r) => r.data)

export const analyzeJob = (jobDescription) =>
  api.post('/api/jobs/analyze', { job_description: jobDescription }).then((r) => r.data)

export const analyzeMatching = (jobDescription, candidateIds) =>
  api
    .post('/api/matching/analyze', {
      job_description: jobDescription,
      candidate_ids: candidateIds,
    })
    .then((r) => r.data)

export const uploadResumes = (files, onUploadProgress) => {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))
  return api
    .post('/api/resumes/upload', formData, { onUploadProgress })
    .then((r) => r.data)
}

export default api