import { useState } from 'react'
import { AlertCircle, FileSearch } from 'lucide-react'
import { analyzeJob, getApiError } from '../services/api'
import { useApp } from '../context/AppContext'
import LoadingSpinner from './LoadingSpinner'

const MIN_WORDS = 10

export default function JobDescriptionForm() {
  const { jdText, setJdText, setJobRequirements } = useApp()
  const [draft, setDraft] = useState(jdText)
  const [jobTitle, setJobTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [validation, setValidation] = useState(null)
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    const text = draft.trim()
    if (!text) {
      setValidation('Please paste a job description before submitting.')
      return
    }
    if (text.split(/\s+/).length < MIN_WORDS) {
      setValidation(`The job description needs at least ${MIN_WORDS} words.`)
      return
    }
    setValidation(null)
    setError(null)
    setLoading(true)
    const fullText = jobTitle.trim() && !text.startsWith(jobTitle.trim())
      ? `${jobTitle.trim()}\n${text}`
      : text
    try {
      const result = await analyzeJob(fullText)
      setJdText(fullText)
      setJobRequirements(result.requirements)
      setSubmitted(true)
    } catch (err) {
      setError(getApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="job-title" className="mb-1.5 block text-sm font-medium text-slate-700">
          Job title <span className="font-normal text-slate-400">(optional)</span>
        </label>
        <input
          id="job-title"
          className="input"
          placeholder="e.g. Senior Python Backend Developer"
          value={jobTitle}
          onChange={(e) => setJobTitle(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="jd-text" className="mb-1.5 block text-sm font-medium text-slate-700">
          Job description
        </label>
        <textarea
          id="jd-text"
          className="input min-h-[180px] resize-y"
          placeholder="Paste the full job description, including required skills, experience and education requirements…"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
        />
        <p className="mt-1 text-xs text-slate-400">
          {draft.trim() ? draft.trim().split(/\s+/).length : 0} words · minimum {MIN_WORDS}
        </p>
      </div>
      {validation && <p className="text-sm text-amber-700">{validation}</p>}
      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </div>
      )}
      <div className="flex items-center gap-3">
        <button type="submit" className="btn-primary" disabled={loading}>
          <FileSearch className="h-4 w-4" />
          {loading ? 'Analyzing…' : 'Submit job description'}
        </button>
        {loading && <LoadingSpinner label="Extracting requirements…" />}
        {submitted && !loading && !error && (
          <span className="text-sm font-medium text-emerald-600">Job description analyzed.</span>
        )}
      </div>
    </form>
  )
}