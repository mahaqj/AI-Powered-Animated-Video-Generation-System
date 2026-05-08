import { useState, useEffect, useMemo, useCallback } from 'react'
import Navbar from './components/Navbar'
import PromptStudio from './components/PromptStudio'
import PipelineDashboard from './components/PipelineDashboard'
import VideoPreview from './components/VideoPreview'
import EditPanel from './components/EditPanel'
import VersionHistory from './components/VersionHistory'
import ToastNotifier from './components/ToastNotifier'
import { usePipeline } from './hooks/usePipeline'
import { useToast } from './hooks/useToast'
import { fetchHistory } from './api/client'

/**
 * AnimAI App
 * Refactored for maximum stability and visual fidelity.
 */
export default function App() {
  const { toasts, addToast, removeToast } = useToast()
  
  // Initialize pipeline hook with a stable toast callback
  const { state, startRun, rerunPhase, revert } = usePipeline(addToast)
  
  const [history, setHistory] = useState([])
  const [previewVideoUrl, setPreviewVideoUrl] = useState(null)
  const [previewVersion, setPreviewVersion] = useState(null)
  const [previewActive, setPreviewActive] = useState(false)

  const showPipeline = state.runId !== null
  const isComplete   = state.overallStatus === 'done'
  const isRunning    = state.overallStatus === 'running'

  // Fetch version history when complete
  useEffect(() => {
    if (isComplete) {
      fetchHistory()
        .then(setHistory)
        .catch(err => console.error("History fetch failed:", err))
    }
  }, [isComplete])

  useEffect(() => {
    setPreviewVideoUrl(null)
  }, [state.runId])

  const handleRegenerate = useCallback(() => {
    if (state.prompt) startRun(state.prompt)
  }, [state.prompt, startRun])

  // Memoize layout components to prevent unnecessary re-renders during SSE updates
  const dashboard = useMemo(() => (
    showPipeline && (
      <div className="fade-up" style={{ animationDelay: '0.1s' }}>
        <PipelineDashboard
          pipelineState={state}
          onRerun={rerunPhase}
        />
      </div>
    )
  ), [showPipeline, state, rerunPhase])

  const preview = useMemo(() => (
    showPipeline && (
      <div className="fade-up" style={{ animationDelay: '0.2s' }}>
        <VideoPreview
          videoUrl={state.phase3.videoUrl}
          previewUrl={previewVideoUrl}
          previewVersion={previewVersion}
          previewActive={previewActive}
          onTogglePreview={(active) => setPreviewActive(active)}
          onRegenerate={isComplete ? handleRegenerate : undefined}
        />
      </div>
    )
  ), [showPipeline, state.phase3.videoUrl, previewVideoUrl, previewVersion, previewActive, isComplete, handleRegenerate])

  return (
    <div style={{ 
      minHeight: '100vh',
      paddingBottom: '100px',
      position: 'relative',
      background: 'var(--bg)',
    }}>
      <Navbar status={state.overallStatus} />

      <main style={{ 
        maxWidth: '1200px', 
        margin: '0 auto',
        padding: '0 24px'
      }}>
        {/* Step 1: Prompt Studio */}
        <div style={{
          transition: 'opacity 0.6s ease, filter 0.6s ease',
          opacity: isRunning ? 0.4 : 1,
          filter: isRunning ? 'blur(2px)' : 'none',
          pointerEvents: isRunning ? 'none' : 'auto'
        }}>
          <PromptStudio
            onSubmit={startRun}
            disabled={isRunning}
          />
        </div>

        {/* Step 2 & 3: Progress & Preview */}
        {dashboard}
        {preview}

        {/* Step 4: Post-Production Tools */}
        {isComplete && (
          <div className="fade-up" style={{ 
            animationDelay: '0.4s',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '32px',
            marginTop: '80px'
          }}>
            <div className="glass" style={{ padding: '32px', borderRadius: '24px' }}>
              <EditPanel 
                runId={state.runId} 
                addToast={addToast}
                onEdited={async (result) => {
                  console.log('[App] onEdited callback triggered, fetching history...')
                  try {
                    if (result?.video_url) {
                      setPreviewVideoUrl(result.video_url)
                      setPreviewVersion(result.version)
                      // do not auto-activate preview; user chooses to view it
                      setPreviewActive(false)
                    }
                    const updatedHistory = await fetchHistory()
                    console.log('[App] Fetched history:', updatedHistory)
                    setHistory(updatedHistory)
                    console.log('[App] History state updated')
                  } catch (err) {
                    console.error('[App] History fetch failed:', err)
                    addToast?.(`Failed to refresh history: ${err.message}`, 'error')
                  }
                }} 
              />
            </div>
            <div className="glass" style={{ padding: '32px', borderRadius: '24px' }}>
              <VersionHistory history={history} onRevert={revert} />
            </div>
          </div>
        )}
      </main>

      <ToastNotifier toasts={toasts} onRemove={removeToast} />
      
      <footer style={{
        textAlign: 'center',
        padding: '80px 24px',
        opacity: 0.2,
        fontFamily: 'var(--font-ticker)',
        fontSize: '12px',
        letterSpacing: '4px',
        textTransform: 'uppercase'
      }}>
        ANIMAI // AGENTIC_PIPELINE_ORCHESTRATOR // BUILT_WITH_INTENT
      </footer>
    </div>
  )
}
