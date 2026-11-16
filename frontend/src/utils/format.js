export function scoreColor(score) {
  if (score == null) return 'text-slate-400'
  if (score >= 75) return 'text-emerald-600'
  if (score >= 50) return 'text-amber-600'
  return 'text-rose-600'
}

export function scoreBarColor(score) {
  if (score >= 75) return '#059669'
  if (score >= 50) return '#d97706'
  return '#e11d48'
}

export function formatScore(score) {
  return score == null ? 'Not available' : `${score}%`
}

export function formatExperience(years) {
  if (years == null) return 'Not available'
  return `${years} yr${years === 1 ? '' : 's'}`
}

export function formatDate(iso) {
  if (!iso) return 'Not available'
  return new Date(iso).toLocaleString()
}

export const MAX_FILE_SIZE = 5 * 1024 * 1024
export const MAX_BATCH = 20
export const ALLOWED_EXTENSIONS = ['.pdf', '.docx']