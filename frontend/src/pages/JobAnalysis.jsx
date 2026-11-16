import { useMemo, useState } from 'react'
import { AlertCircle, Sparkles, Briefcase, GraduationCap, Clock } from 'lucide-react'
import JobDescriptionForm from '../components/JobDescriptionForm'
import ResumeUploader from '../components/ResumeUploader'
import CandidateTable from '../components/CandidateTable'
import SkillBadges from '../components/SkillBadges'
import LoadingSpinner from '../components/LoadingSpinner'
import { CandidateComparisonChart } from '../components/ScoreChart'
import { analyzeMatching, getApiError } from '../services/api'
import { useApp } from '../context/AppContext'

function RequirementsPanel({ requirements }) {
  return (
    <div className="card p-5">
      <h3 className="text-base font-bold text-slate-900">Extracted job requirements</h3>
      <p className="text-xs text-slate-400">Computed by the backend JD analyzer</p>
      <div className="mt-4 grid grid-cols-1 gap-5 md:grid-cols-2">
        <div>
          <p className="section-title mb-2">Required skills</p>
          <SkillBadges skills={requirements.required_skills} tone="neutral" emptyText="None detected" />
        </div>
        <div>
          <p className="section-title mb-2">Preferred skills</p>
          <SkillBadges skills={requirements.preferred_skills} tone="preferred" emptyText="None detected" />
        </div>
        <div className="space-y-2 text-sm text-slate-700">
          <p className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-slate-400" />
            Experience:{' '}
            {requirements.min_experience_years != null
              ? `minimum ${requirements.min_experience_years} years`
              : 'not specified'}
            {requirements.preferred_experience_years != null &&
              ` (preferred ${requirements.preferred_experience_years} years)`}
          </p>
          <p className="flex items-center gap-2">
            <GraduationCap className="h-4 w-4 text-slate-400" />
            Education:{' '}
            {requirements.required_education?.length
              ? requirements.required_education.join(' or ')
              : 'not specified'}
          </p>
          <p className="flex items-center gap-2">
            <Briefcase className="h-4 w-4 text-slate-400" />
            Title: {requirements.job_title || 'not detected'}
          </p>
        </div>
        {requirements.responsibilities?.length > 0 && (
          <div>
            <p className="section-title mb-2">Responsibilities</p>
            <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
              {requirements.responsibilities.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

export default function JobAnalysis() {
  const {
    jdText,
    jobRequirements,
    uploadedCandidates,
    matchResult,
    setMatchResult,
  } = useApp()
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState(null)

  const experienceById = useMemo(
    () => Object.fromEntries(uploadedCandidates.map((c) => [c.id, c.experience_years])),
    [uploadedCandidates]
  )

  const canAnalyze = jdText.trim() && uploadedCandidates.length > 0

  const handleAnalyze = async () => {
    setAnalyzing(true)
    setError(null)
    try {
      const result = await analyzeMatching(
        jdText,
        uploadedCandidates.map((c) => c.id)
      )
      setMatchResult(result)
    } catch (err) {
      setError(getApiError(err))
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <section className="card p-5">
          <div className="mb-4 flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white">1</span>
            <h2 className="text-base font-bold text-slate-900">Job description</h2>
          </div>
          <JobDescriptionForm />
        </section>
        <section className="card p-5">
          <div className="mb-4 flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white">2</span>
            <h2 className="text-base font-bold text-slate-900">Upload resumes</h2>
          </div>
          <ResumeUploader />
        </section>
      </div>

      {jobRequirements && <RequirementsPanel requirements={jobRequirements} />}

      <section className="card p-5">
        <div className="mb-4 flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white">3</span>
          <h2 className="text-base font-bold text-slate-900">AI matching</h2>
        </div>
        {!canAnalyze && (
          <p className="mb-3 text-sm text-slate-500">
            {!jdText.trim() ? 'Submit a job description' : 'Upload at least one resume'} to enable
            analysis.
          </p>
        )}
        <div className="flex flex-wrap items-center gap-3">
          <button className="btn-primary" onClick={handleAnalyze} disabled={!canAnalyze || analyzing}>
            <Sparkles className="h-4 w-4" />
            {analyzing ? 'Analyzing…' : `Analyze ${uploadedCandidates.length || ''} candidates`}
          </button>
          {analyzing && (
            <LoadingSpinner label="Running AI matching — the first run loads the model and can take ~10 s…" />
          )}
        </div>
        {error && (
          <div className="mt-3 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            {error}
          </div>
        )}
        {matchResult?.not_found_ids?.length > 0 && (
          <p className="mt-3 text-sm text-amber-700">
            Some candidate IDs were not found in the database: {matchResult.not_found_ids.join(', ')}
          </p>
        )}
      </section>

      {matchResult && (
        <>
          <section>
            <div className="mb-3 flex items-baseline justify-between">
              <h2 className="text-base font-bold text-slate-900">
                Ranked candidates ({matchResult.total_candidates})
              </h2>
              <span className="text-xs text-slate-400">Order computed by the backend AI engine</span>
            </div>
            <CandidateTable
              rankedCandidates={matchResult.ranked_candidates}
              experienceById={experienceById}
            />
          </section>
          <section className="card p-5">
            <h2 className="text-base font-bold text-slate-900">Match score comparison</h2>
            <p className="mb-4 text-xs text-slate-400">Final weighted scores (0–100)</p>
            <CandidateComparisonChart rankedCandidates={matchResult.ranked_candidates} />
          </section>
        </>
      )}
    </div>
  )
}