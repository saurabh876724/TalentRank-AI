import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpDown, Eye, Trophy } from 'lucide-react'
import SkillBadges from './SkillBadges'
import { formatScore, formatExperience, scoreColor } from '../utils/format'

export default function CandidateTable({ rankedCandidates = [], experienceById = {} }) {
  const [sortBy, setSortBy] = useState(null)

  const rows = useMemo(() => {
    if (!sortBy) return rankedCandidates
    const copy = [...rankedCandidates]
    copy.sort((a, b) => (b[sortBy] ?? -1) - (a[sortBy] ?? -1))
    return copy
  }, [rankedCandidates, sortBy])

  if (!rankedCandidates.length) {
    return (
      <div className="card p-10 text-center text-sm text-slate-400">
        No ranked candidates yet. Submit a job description, upload resumes and run the analysis.
      </div>
    )
  }

  return (
    <div className="card overflow-x-auto">
      <table className="w-full min-w-[760px] text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
            <th className="px-4 py-3">Rank</th>
            <th className="px-4 py-3">Candidate</th>
            <th className="px-4 py-3">Experience</th>
            <th className="px-4 py-3">
              <button
                className="inline-flex items-center gap-1 uppercase hover:text-slate-700"
                onClick={() => setSortBy(sortBy === 'final_score' ? null : 'final_score')}
                title="Toggle sort by match score (default: backend ranking)"
              >
                Match <ArrowUpDown className="h-3 w-3" />
              </button>
            </th>
            <th className="px-4 py-3">Matched skills</th>
            <th className="px-4 py-3">Missing skills</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((candidate) => {
            const experience = experienceById[candidate.candidate_id]
            return (
              <tr key={candidate.candidate_id} className="hover:bg-slate-50">
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
                      candidate.rank === 1 ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {candidate.rank === 1 ? <Trophy className="h-3.5 w-3.5" /> : candidate.rank}
                  </span>
                </td>
                <td className="px-4 py-3 font-semibold text-slate-800">
                  {candidate.candidate_name || 'Not available'}
                </td>
                <td className="px-4 py-3 text-slate-600">{formatExperience(experience)}</td>
                <td className={`px-4 py-3 text-base font-bold ${scoreColor(candidate.final_score)}`}>
                  {formatScore(candidate.final_score)}
                </td>
                <td className="max-w-[220px] px-4 py-3">
                  <SkillBadges skills={candidate.matched_skills} tone="matched" />
                </td>
                <td className="max-w-[220px] px-4 py-3">
                  <SkillBadges skills={candidate.missing_skills} tone="missing" />
                </td>
                <td className="px-4 py-3">
                  <Link
                    to={`/candidates/${candidate.candidate_id}`}
                    className="btn-secondary !px-3 !py-1.5 text-xs"
                  >
                    <Eye className="h-3.5 w-3.5" /> Details
                  </Link>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
      {sortBy && (
        <p className="border-t border-slate-100 px-4 py-2 text-xs text-slate-400">
          Sorted by match score.{' '}
          <button className="font-semibold text-indigo-600" onClick={() => setSortBy(null)}>
            Restore backend ranking
          </button>
        </p>
      )}
    </div>
  )
}