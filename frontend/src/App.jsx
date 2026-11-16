import { useState } from 'react'
import { Routes, Route, useLocation, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Dashboard from './pages/Dashboard'
import JobAnalysis from './pages/JobAnalysis'
import Candidates from './pages/Candidates'
import CandidateDetails from './pages/CandidateDetails'
import { AppProvider } from './context/AppContext'

const TITLES = [
  { match: (p) => p === '/', title: 'Dashboard' },
  { match: (p) => p.startsWith('/job-analysis'), title: 'Job Analysis & Matching' },
  { match: (p) => /^\/candidates\/\d+/.test(p), title: 'Candidate Details' },
  { match: (p) => p.startsWith('/candidates'), title: 'Candidates' },
]

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const title = TITLES.find((t) => t.match(location.pathname))?.title || 'TalentRank AI'

  return (
    <AppProvider>
      <div className="min-h-screen">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <div className="lg:pl-64">
          <Header title={title} onMenuClick={() => setSidebarOpen(true)} />
          <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/job-analysis" element={<JobAnalysis />} />
              <Route path="/candidates" element={<Candidates />} />
              <Route path="/candidates/:id" element={<CandidateDetails />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </AppProvider>
  )
}