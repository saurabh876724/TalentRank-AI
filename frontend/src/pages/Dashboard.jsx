import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Users, Target, TrendingUp, Award, FileSearch } from 'lucide-react'
import { fetchStats, getApiError } from '../services/api'
import StatCard from '../components/StatCard'
import LoadingSpinner from '../components/LoadingSpinner'
import { ScoreDistributionChart } from '../components/ScoreChart'
import { formatDate } from '../utils/format'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch((err) => setError(getApiError(err)))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner label="Loading dashboard…" className="py-20" />
  if (error) {
    return (
      <div className="card p-6 text-sm text-rose-700">
        <p className="font-semibold">Could not load dashboard data</p>
        <p className="mt-1">{error}</p>
      </div>
    )
  }

  const latest = stats.latest_analysis
  const hasScores = latest && latest.candidate_count > 0

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Candidates processed" value={stats.total_candidates} icon={Users} hint="Successfully parsed resumes" />
        <StatCard label="Candidates analyzed" value={stats.analyzed_candidates} icon={Target} hint="Matched against a job description" />
        <StatCard
          label="Average match score"
          value={hasScores ? `${latest.average_score}%` : '—'}
          icon={TrendingUp}
          hint={hasScores ? 'Latest analysis' : 'No analysis yet'}
        />
        <StatCard
          label="Highest match score"
          value={hasScores ? `${latest.highest_score}%` : '—'}
          icon={Award}
          hint={hasScores ? 'Latest analysis' : 'No analysis yet'}
        />
      </div>

      {hasScores ? (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
          <div className="card p-5 xl:col-span-2">
            <h2 className="text-base font-bold text-slate-900">Score distribution</h2>
            <p className="mb-4 text-xs text-slate-400">Final match scores from the latest analysis</p>
            <ScoreDistributionChart distribution={latest.score_distribution} />
          </div>
          <div className="card p-5">
            <h2 className="text-base font-bold text-slate-900">Latest analysis</h2>
            <dl className="mt-4 space-y-3 text-sm">
              <div>
                <dt className="text-slate-400">Job</dt>
                <dd className="font-semibold text-slate-800">{latest.job_title || 'Not available'}</dd>
              </div>
              <div>
                <dt className="text-slate-400">Candidates ranked</dt>
                <dd className="font-semibold text-slate-800">{latest.candidate_count}</dd>
              </div>
              <div>
                <dt className="text-slate-400">Run at</dt>
                <dd className="font-semibold text-slate-800">{formatDate(latest.created_at)}</dd>
              </div>
              <div>
                <dt className="text-slate-400">Total analyses</dt>
                <dd className="font-semibold text-slate-800">{stats.total_analyses}</dd>
              </div>
            </dl>
            <Link to="/job-analysis" className="btn-primary mt-5 w-full">
              <FileSearch className="h-4 w-4" /> Run a new analysis
            </Link>
          </div>
        </div>
      ) : (
        <div className="card flex flex-col items-center p-12 text-center">
          <FileSearch className="h-10 w-10 text-slate-300" />
          <h2 className="mt-4 text-base font-bold text-slate-800">No analysis performed yet</h2>
          <p className="mt-1 max-w-md text-sm text-slate-500">
            Enter a job description, upload candidate resumes and run AI matching to see real
            scores and rankings here.
          </p>
          <Link to="/job-analysis" className="btn-primary mt-5">
            Start your first analysis
          </Link>
        </div>
      )}
    </div>
  )
}