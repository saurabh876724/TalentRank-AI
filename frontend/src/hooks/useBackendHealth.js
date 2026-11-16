import { useEffect, useState } from 'react'
import { fetchHealth } from '../services/api'

export default function useBackendHealth(intervalMs = 30000) {
  const [healthy, setHealthy] = useState(null)

  useEffect(() => {
    let active = true
    const check = () =>
      fetchHealth()
        .then(() => active && setHealthy(true))
        .catch(() => active && setHealthy(false))
    check()
    const timer = setInterval(check, intervalMs)
    return () => {
      active = false
      clearInterval(timer)
    }
  }, [intervalMs])

  return healthy
}