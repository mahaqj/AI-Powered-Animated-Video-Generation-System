import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import PropTypes from 'prop-types'

const CHIPS = [
  "Change voice tone",
  "Make it darker",
  "Add background music",
  "Speed up scene 2",
]

export default function EditPanel({ runId, onEdited, addToast }) {
  const [open, setOpen]     = useState(false)
  const [text, setText]     = useState('')
  const [sending, setSend]  = useState(false)

  async function handleSend() {
    if (!text.trim() || !runId) return
    setSend(true)
    try {
      const { applyEdit } = await import('../api/client')
      console.log('[EditPanel] Sending edit:', { run_id: runId, edit_text: text })
      const res = await applyEdit(runId, text)
      console.log('[EditPanel] Edit response:', res)
      
      if (res?.version) {
        addToast?.(`Edit saved! Version ${res.version} ✨`, 'success')
        console.log('[EditPanel] Calling onEdited callback...')
        if (onEdited) {
          await onEdited(res)
          console.log('[EditPanel] onEdited callback completed')
        }
      } else {
        throw new Error('No version in response')
      }
    } catch (err) {
      console.error('[EditPanel] Edit failed:', err)
      addToast?.(`Edit failed: ${err.message}`, 'error')
    }
    setSend(false)
    setText('')
  }

  return (
    <section style={{
      maxWidth: '900px',
      margin: '0 auto',
      padding: '0 24px 40px',
    }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: '20px',
          background: 'transparent',
          border: '2px solid var(--bubblegum)',
          color: 'var(--bubblegum)',
          padding: '10px 20px',
          borderRadius: '8px',
          cursor: 'pointer',
          boxShadow: '3px 3px 0px var(--grape)',
          transition: 'all 0.2s ease',
        }}
      >
        ✏️ {open ? 'Close Editor' : 'Edit Something'}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{
              marginTop: '16px',
              background: 'var(--surface)',
              border: '2px solid var(--bubblegum)',
              borderRadius: '10px',
              padding: '20px',
            }}>
              <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '22px', marginBottom: '12px', color: 'var(--bubblegum)' }}>
                Tell the editor what to fix
              </h3>

              <textarea
                value={text}
                onChange={e => setText(e.target.value)}
                placeholder="e.g. Make the first scene darker"
                rows={3}
                style={{
                  width: '100%',
                  background: 'var(--bg)',
                  border: '2px solid #444',
                  borderRadius: '6px',
                  color: 'var(--snow)',
                  fontFamily: 'var(--font-body)',
                  fontSize: '14px',
                  padding: '12px',
                  resize: 'vertical',
                  outline: 'none',
                  marginBottom: '12px',
                }}
              />

              {/* Example Chips */}
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '16px' }}>
                {CHIPS.map(chip => (
                  <button
                    key={chip}
                    onClick={() => setText(chip)}
                    style={{
                      background: 'var(--grape)',
                      border: 'none',
                      color: 'var(--snow)',
                      fontFamily: 'var(--font-body)',
                      fontSize: '12px',
                      padding: '4px 12px',
                      borderRadius: '999px',
                      cursor: 'pointer',
                      opacity: 0.8,
                    }}
                  >
                    {chip}
                  </button>
                ))}
              </div>

              <button
                onClick={handleSend}
                disabled={sending || !text.trim()}
                style={{
                  fontFamily: 'var(--font-display)',
                  fontSize: '18px',
                  padding: '10px 24px',
                  background: 'var(--bubblegum)',
                  color: 'var(--ink)',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: sending ? 'wait' : 'pointer',
                  boxShadow: '3px 3px 0px var(--grape)',
                }}
              >
                {sending ? 'Sending...' : 'Send Edit 🎯'}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  )
}

EditPanel.propTypes = {
  runId: PropTypes.string,
  onEdited: PropTypes.func,
  addToast: PropTypes.func,
}
