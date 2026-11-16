import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Eye, Search, Users } from 'lucide-react'
import { fetchCandidates, getApiError } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import SkillBadges from '../components/SkillBadges'
import { formatDate, formatExperience } from '../utils/format'

export default function Candidates() {
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [query, setQuery] = useState('')

  useEffect(() => {
    fetchCandidates()
      .then((data) => setCandidates(data.candidates))
      .catch((err) => setError(getApiError(err)))
      .finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return candidates
    return candidates.filter(
      (c) =>
        (c.candidate_name || '').toLowerCase().includes(q) ||
        (c.email || '').toLowerCase().includes(q) ||
        (c.skills || []).some((s) => s.toLowerCase().includes(q))
    )
  }, [candidates, query])

  if (loading) return <LoadingSpinner label="Loading candidates…" className="py-20" />
  if (error) {
    return (
      <div className="card p-6 text-sm text-rose-700">
        <p className="font-semibold">Could not load candidates</p>
        <p className="mt-1">{error}</p>
      </div>
    )
  }

  if (!candidates.length) {
    return (
      <div className="card flex flex-col items-center p-12 text-center">
        <Users className="h-10 w-10 text-slate-300" />
        <h2 className="mt-4 text-base font-bold text-slate-800">No candidates uploaded yet</h2>
        <p className="mt-1 text-sm text-slate-500">Upload resumes to build your candidate pool.</p>
        <Link to="/job-analysis" className="btn-primary mt-5">
          Upload resumes
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          className="input !pl-9"
          placeholder="Search name, email or skill…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search candidates"
        />
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Experience</th>
              <th className="px-4 py-3">Skills</th>
              <th className="px-4 py-3">Uploaded</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtered.map((candidate) => (
              <tr key={candidate.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-semibold text-slate-800">
                  {candidate.candidate_name || 'Not available'}
                  {!candidate.has_resume_text && (
                    <span className="badge ml-2 bg-amber-50 text-amber-700" title="Uploaded before resume text storage; re-upload to enable semantic scoring">
                      no text
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-slate-600">{candidate.email || 'Not available'}</td>
                <td className="px-4 py-3 text-slate-600">{formatExperience(candidate.experience_years)}</td>
                <td className="max-w-[260px] px-4 py-3">
                  <SkillBadges skills={candidate.skills} tone="neutral" />
                </td>
                <td className="px-4 py-3 text-xs text-slate-400">{formatDate(candidate.created_at)}</td>
                <td className="px-4 py-3">
                  <Link to={`/candidates/${candidate.id}`} className="btn-secondary !px-3 !py-1.5 text-xs">
                    <Eye className="h-3.5 w-3.5" /> Details
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!filtered.length && (
          <p className="px-4 py-6 text-center text-sm text-slate-400">No candidates match your search.</p>
        )}
      </div>
    </div>
  )
}