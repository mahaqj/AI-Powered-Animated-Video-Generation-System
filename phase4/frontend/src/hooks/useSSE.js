import { useState, useEffect, useRef } from 'react'

/**
 * useSSE — connects to /api/stream/{runId} and dispatches incoming SSE events.
 * Now accepts an optional onEvent callback for real-time processing.
 */
export function useSSE(runId, onEvent) {
  const [events, setEvents]         = useState([])
  const [connected, setConnected]   = useState(false)
  const [error, setError]           = useState(null)
  const esRef                       = useRef(null)

  useEffect(() => {
    if (!runId) {
      setEvents([])
      setConnected(false)
      setError(null)
      return
    }

    // Close any previous connection
    if (esRef.current) esRef.current.close()

    const es = new EventSource(`/api/stream/${runId}`)
    esRef.current = es
    setConnected(true)
    setError(null)

    const EVENT_TYPES = [
      'run_start', 'phase_start', 'phase_done', 'phase_error',
      'pipeline_complete', 'done', 'error',
    ]

    EVENT_TYPES.forEach(type => {
      es.addEventListener(type, (e) => {
        const payload = { event: type, data: JSON.parse(e.data) }
        
        // Internal state
        setEvents(prev => [...prev, payload])
        
        // External callback (important for state sync in usePipeline)
        if (onEvent) onEvent(payload)

        if (type === 'done' || type === 'error') {
          es.close()
          setConnected(false)
        }
      })
    })

    es.onerror = () => {
      setError('SSE connection lost')
      setConnected(false)
      es.close()
    }

    return () => {
      es.close()
      setConnected(false)
    }
  }, [runId]) // eslint-disable-line react-hooks/exhaustive-deps

  return { events, connected, error }
}
