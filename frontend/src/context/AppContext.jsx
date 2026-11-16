import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const STORAGE_KEY = 'talentrank_state_v1'

const AppContext = createContext(null)

function loadPersisted() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

export function AppProvider({ children }) {
  const persisted = useMemo(loadPersisted, [])
  const [jdText, setJdText] = useState(persisted.jdText || '')
  const [jobRequirements, setJobRequirements] = useState(persisted.jobRequirements || null)
  const [uploadedCandidates, setUploadedCandidates] = useState(persisted.uploadedCandidates || [])
  const [uploadErrors, setUploadErrors] = useState(persisted.uploadErrors || [])
  const [matchResult, setMatchResult] = useState(persisted.matchResult || null)

  useEffect(() => {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ jdText, jobRequirements, uploadedCandidates, uploadErrors, matchResult })
      )
    } catch {
      // Storage may be unavailable (private mode); the app still works in-memory.
    }
  }, [jdText, jobRequirements, uploadedCandidates, uploadErrors, matchResult])

  const value = {
    jdText,
    setJdText,
    jobRequirements,
    setJobRequirements,
    uploadedCandidates,
    setUploadedCandidates,
    uploadErrors,
    setUploadErrors,
    matchResult,
    setMatchResult,
  }
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  const context = useContext(AppContext)
  if (!context) throw new Error('useApp must be used inside AppProvider')
  return context
}