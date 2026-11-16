export default function StatCard({ label, value, icon: Icon, hint }) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
          {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
        </div>
        {Icon && (
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50">
            <Icon className="h-5 w-5 text-indigo-600" />
          </span>
        )}
      </div>
    </div>
  )
}