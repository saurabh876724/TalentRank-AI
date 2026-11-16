export default function SkillBadges({ skills = [], tone = 'matched', emptyText = 'None' }) {
  if (!skills.length) return <span className="text-sm text-slate-400">{emptyText}</span>
  const tones = {
    matched: 'bg-emerald-50 text-emerald-700',
    missing: 'bg-rose-50 text-rose-700',
    preferred: 'bg-sky-50 text-sky-700',
    neutral: 'bg-slate-100 text-slate-700',
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {skills.map((skill) => (
        <span key={skill} className={`badge ${tones[tone] || tones.neutral}`}>
          {skill}
        </span>
      ))}
    </div>
  )
}