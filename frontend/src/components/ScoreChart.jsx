import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from 'recharts'
import { scoreBarColor } from '../utils/format'

const COMPONENT_LABELS = {
  semantic_score: 'Semantic',
  skills_score: 'Skills',
  experience_score: 'Experience',
  education_score: 'Education',
}

export function ScoreDistributionChart({ distribution }) {
  return (
    <ResponsiveContainer width="100%" height={260} initialDimension={{ width: 800, height: 260 }}>
      <BarChart data={distribution} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
        <XAxis dataKey="range" tick={{ fontSize: 12, fill: '#64748b' }} />
        <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: '#64748b' }} />
        <Tooltip formatter={(value) => [`${value} candidate(s)`, 'Count']} />
        <Bar dataKey="count" fill="#4f46e5" radius={[4, 4, 0, 0]} maxBarSize={56} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function CandidateComparisonChart({ rankedCandidates }) {
  const data = rankedCandidates.map((c) => ({
    name: c.candidate_name || `#${c.candidate_id}`,
    score: c.final_score ?? 0,
  }))
  return (
    <ResponsiveContainer
      width="100%"
      height={Math.max(220, data.length * 36)}
      initialDimension={{ width: 800, height: Math.max(220, data.length * 36) }}
    >
      <BarChart data={data} layout="vertical" margin={{ top: 8, right: 24, left: 40, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
        <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12, fill: '#64748b' }} />
        <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 12, fill: '#334155' }} />
        <Tooltip formatter={(value) => [`${value}%`, 'Final score']} />
        <Bar dataKey="score" radius={[0, 4, 4, 0]} maxBarSize={22}>
          {data.map((entry, index) => (
            <Cell key={index} fill={scoreBarColor(entry.score)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function ComponentBreakdownChart({ candidate }) {
  const data = Object.entries(COMPONENT_LABELS)
    .filter(([key]) => candidate[key] != null)
    .map(([key, label]) => ({ component: label, score: candidate[key] }))
  if (!data.length) {
    return <p className="text-sm text-slate-400">No component scores available.</p>
  }
  return (
    <ResponsiveContainer width="100%" height={240} initialDimension={{ width: 600, height: 240 }}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
        <XAxis dataKey="component" tick={{ fontSize: 12, fill: '#64748b' }} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: '#64748b' }} />
        <Tooltip formatter={(value) => [`${value}%`, 'Score']} />
        <Bar dataKey="score" radius={[4, 4, 0, 0]} maxBarSize={56}>
          {data.map((entry, index) => (
            <Cell key={index} fill={scoreBarColor(entry.score)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}