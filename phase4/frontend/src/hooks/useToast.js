import { useState, useCallback } from 'react'

let _nextId = 0

/**
 * useToast — manages a queue of toasts that auto-dismiss after 4 seconds.
 * Returns { toasts, addToast, removeToast }
 */
export function useToast() {
  const [toasts, setToasts] = useState([])

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const addToast = useCallback((message, type = 'info') => {
    const id = ++_nextId
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => removeToast(id), 4000)
  }, [removeToast])

  return { toasts, addToast, removeToast }
}
