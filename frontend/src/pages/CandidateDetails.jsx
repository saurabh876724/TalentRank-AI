import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Mail, Phone, GraduationCap, Clock, FileSearch } from 'lucide-react'
import { fetchCandidate, getApiError } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import SkillBadges from '../components/SkillBadges'
import { ComponentBreakdownChart } from '../components/ScoreChart'
import { formatScore, scoreColor, formatExperience, formatDate } from '../utils/format'

function InfoRow({ icon: Icon, label, value }) {
  return (
    <p className="flex items-center gap-2 text-sm text-slate-700">
      <Icon className="h-4 w-4 shrink-0 text-slate-400" />
      <span className="text-slate-400">{label}:</span>
      <span className="font-medium">{value ?? 'Not available'}</span>
    </p>
  )
}

export default function CandidateDetails() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    fetchCandidate(id)
      .then(setData)
      .catch((err) => setError(getApiError(err)))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <LoadingSpinner label="Loading candidate…" className="py-20" />
  if (error) {
    return (
      <div className="card p-6 text-sm text-rose-700">
        <p className="font-semibold">Could not load candidate</p>
        <p className="mt-1">{error}</p>
        <Link to="/candidates" className="btn-secondary mt-4">
          <ArrowLeft className="h-4 w-4" /> Back to candidates
        </Link>
      </div>
    )
  }

  const { candidate, latest_match: match } = data

  return (
    <div className="space-y-6">
      <Link to="/candidates" className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-700">
        <ArrowLeft className="h-4 w-4" /> Back to candidates
      </Link>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <section className="card p-5 xl:col-span-1">
          <h2 className="text-lg font-bold text-slate-900">
            {candidate.candidate_name || 'Not available'}
          </h2>
          <div className="mt-4 space-y-2.5">
            <InfoRow icon={Mail} label="Email" value={candidate.email} />
            <InfoRow icon={Phone} label="Phone" value={candidate.phone} />
            <InfoRow icon={Clock} label="Experience" value={formatExperience(candidate.experience_years)} />
          </div>
          <div className="mt-5">
            <p className="section-title mb-2">Technical skills</p>
            <SkillBadges skills={candidate.skills} tone="neutral" emptyText="Not available" />
          </div>
          <div className="mt-5">
            <p className="section-title mb-2 flex items-center gap-1.5">
              <GraduationCap className="h-4 w-4" /> Education
            </p>
            {candidate.education?.length ? (
              <ul className="space-y-2 text-sm text-slate-700">
                {candidate.education.map((entry, i) => (
                  <li key={i}>
                    <p className="font-semibold">{entry.degree}</p>
                    <p className="text-slate-500">{entry.institution || entry.details || ''}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-400">Not available</p>
            )}
          </div>
        </section>

        <section className="card p-5 xl:col-span-2">
          <h2 className="text-base font-bold text-slate-900">Matching analysis</h2>
          {match ? (
            <>
              <p className="text-xs text-slate-400">
                Latest analysis · {match.job_title || 'Untitled job'} · {formatDate(match.created_at)}
              </p>
              <div className="mt-4 flex flex-wrap items-center gap-6">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-400">Overall match</p>
                  <p className={`text-4xl font-extrabold ${scoreColor(match.final_score)}`}>
                    {formatScore(match.final_score)}
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-400">Rank</p>
                  <p className="text-4xl font-extrabold text-slate-800">#{match.rank}</p>
                </div>
              </div>
              <div className="mt-4">
                <ComponentBreakdownChart candidate={match} />
              </div>
              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
                <div>
                  <p className="section-title mb-2">Matched skills</p>
                  <SkillBadges skills={match.matched_skills} tone="matched" />
                </div>
                <div>
                  <p className="section-title mb-2">Missing required</p>
                  <SkillBadges skills={match.missing_skills} tone="missing" />
                </div>
                <div>
                  <p className="section-title mb-2">Component scores</p>
                  <ul className="space-y-1 text-sm text-slate-600">
                    <li>Semantic: {formatScore(match.semantic_score)}</li>
                    <li>Skills: {formatScore(match.skills_score)}</li>
                    <li>Experience: {formatScore(match.experience_score)}</li>
                    <li>Education: {formatScore(match.education_score)}</li>
                  </ul>
                </div>
              </div>
            </>
          ) : (
            <div className="mt-6 flex flex-col items-center py-8 text-center">
              <FileSearch className="h-8 w-8 text-slate-300" />
              <p className="mt-3 text-sm text-slate-500">
                This candidate has not been matched against a job description yet.
              </p>
              <Link to="/job-analysis" className="btn-primary mt-4">
                Run an analysis
              </Link>
            </div>
          )}
        </section>
      </div>

      {match?.explanation?.length > 0 && (
        <section className="card p-5">
          <h2 className="text-base font-bold text-slate-900">Explanation</h2>
          <p className="mb-3 text-xs text-slate-400">Generated by the backend scoring engine</p>
          <div className="space-y-1 rounded-lg bg-slate-50 p-4 font-mono text-[13px] leading-relaxed text-slate-700">
            {match.explanation.map((line, i) => (
              <p key={i} className={line.endsWith(':') ? 'mt-2 font-bold text-slate-900' : ''}>
                {line}
              </p>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}