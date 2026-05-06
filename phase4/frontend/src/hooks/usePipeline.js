import { useState, useCallback } from 'react'
import { useSSE } from './useSSE'
import { runPipeline, rerunPhase as rerunPhaseAPI, revertVersion } from '../api/client'

const INITIAL_PHASE = { status: 'idle', data: null }

const INITIAL_STATE = {
  runId:         null,
  prompt:        '',
  phase1:        { ...INITIAL_PHASE },
  phase2:        { ...INITIAL_PHASE },
  phase3:        { ...INITIAL_PHASE, videoUrl: null },
  overallStatus: 'idle',
  error:         null,
}

/**
 * usePipeline — manages full pipeline run state, integrates SSE events.
 * Returns { state, startRun, rerunPhase, revert }
 */
export function usePipeline(addToast) {
  const [state, setState] = useState(INITIAL_STATE)

  // ── Event Handler ──
  // We handle events via a stable callback to avoid React state batching issues
  const handleEvent = useCallback((payload) => {
    const { event, data } = payload

    if (event === 'phase_start') {
      const phase = data.phase
      setState(prev => ({
        ...prev,
        overallStatus: 'running',
        [`phase${phase}`]: { ...prev[`phase${phase}`], status: 'running' },
      }))
    }

    if (event === 'phase_done') {
      const phase = data.phase
      setState(prev => ({
        ...prev,
        [`phase${phase}`]: { status: 'done', data: data.data },
      }))
      addToast?.(`Phase ${phase} complete! ✅`, 'success')
    }

    if (event === 'phase_error') {
      const phase = data.phase
      setState(prev => ({
        ...prev,
        overallStatus: 'error',
        [`phase${phase}`]: { ...prev[`phase${phase}`], status: 'error' },
        error: data.error,
      }))
      addToast?.(`Phase ${phase} failed: ${data.error}`, 'error')
    }

    if (event === 'pipeline_complete') {
      setState(prev => ({
        ...prev,
        overallStatus: 'done',
        phase3: { ...prev.phase3, videoUrl: data.video_url },
      }))
      addToast?.('Your film is ready! 🎬', 'success')
    }

    if (event === 'error') {
      setState(prev => ({
        ...prev,
        overallStatus: 'error',
        error: data.message,
      }))
    }
  }, [addToast])

  // React to SSE events whenever runId changes
  useSSE(state.runId, handleEvent)

  const startRun = useCallback(async (prompt, addSubtitles = false, seed = null) => {
    setState({
      ...INITIAL_STATE,
      prompt,
      overallStatus: 'running',
    })
    try {
      const { run_id } = await runPipeline(prompt, addSubtitles, seed)
      setState(prev => ({ ...prev, runId: run_id }))
    } catch (e) {
      setState(prev => ({
        ...prev,
        overallStatus: 'error',
        error: e.message,
      }))
      addToast?.(`Failed to start pipeline: ${e.message}`, 'error')
    }
  }, [addToast])

  const rerunPhase = useCallback(async (phase) => {
    if (!state.runId) return
    setState(prev => ({
      ...prev,
      [`phase${phase}`]: { ...INITIAL_PHASE, status: 'running' },
    }))
    try {
      await rerunPhaseAPI(state.runId, phase)
    } catch (e) {
      addToast?.(`Rerun failed: ${e.message}`, 'error')
    }
  }, [state.runId, addToast])

  const revert = useCallback(async (version) => {
    try {
      await revertVersion(version)
      addToast?.(`Reverted to version ${version} ↩️`, 'info')
    } catch (e) {
      addToast?.(`Revert failed: ${e.message}`, 'error')
    }
  }, [addToast])

  return { state, startRun, rerunPhase, revert }
}
