import { Menu } from 'lucide-react'
import useBackendHealth from '../hooks/useBackendHealth'

export default function Header({ title, onMenuClick }) {
  const healthy = useBackendHealth()
  return (
    <header className="sticky top-0 z-20 flex items-center justify-between border-b border-slate-200 bg-white/90 px-4 py-3.5 backdrop-blur sm:px-6">
      <div className="flex items-center gap-3">
        <button className="lg:hidden" onClick={onMenuClick} aria-label="Open menu">
          <Menu className="h-5 w-5 text-slate-600" />
        </button>
        <h1 className="text-lg font-bold text-slate-900">{title}</h1>
      </div>
      <span
        className={`badge ${
          healthy === null
            ? 'bg-slate-100 text-slate-500'
            : healthy
              ? 'bg-emerald-50 text-emerald-700'
              : 'bg-rose-50 text-rose-700'
        }`}
      >
        <span
          className={`mr-1.5 h-1.5 w-1.5 rounded-full ${
            healthy === null ? 'bg-slate-400' : healthy ? 'bg-emerald-500' : 'bg-rose-500'
          }`}
        />
        {healthy === null ? 'Checking API…' : healthy ? 'API connected' : 'API offline'}
      </span>
    </header>
  )
}