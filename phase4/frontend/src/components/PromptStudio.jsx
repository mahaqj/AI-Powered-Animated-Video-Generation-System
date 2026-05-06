import { useState } from 'react'
import ParticlesBurst from './ParticlesBurst'

export default function PromptStudio({ onSubmit, disabled }) {
  const [prompt, setPrompt]         = useState('')
  const [subtitles, setSubtitles]   = useState(false)
  const [seed, setSeed]             = useState('')
  const [submitted, setSubmitted]   = useState(false)
  const [focused, setFocused]       = useState(false)

  const isTooShort = prompt.trim().length > 0 && prompt.trim().length < 10
  const canSubmit = prompt.trim().length >= 10 && !disabled

  function handleSubmit() {
    if (!canSubmit) return
    setSubmitted(s => !s) // toggle to re-trigger burst
    onSubmit(prompt.trim(), subtitles, seed ? parseInt(seed) : null)
  }

  return (
    <section style={{
      padding: '120px 24px 60px',
      maxWidth: '1000px',
      margin: '0 auto',
      position: 'relative',
    }}>
      {/* Hero Header */}
      <div style={{ textAlign: 'center', marginBottom: '60px' }}>
        <h1 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'clamp(40px, 8vw, 72px)',
          color: 'var(--acid)',
          marginBottom: '16px',
          lineHeight: 0.9,
          textTransform: 'uppercase',
          letterSpacing: '-2px',
          animation: 'glow-pulse 3s ease-in-out infinite',
        }}>
          Direct Your <br/>
          <span className="shimmer-text">Own Reality</span>
        </h1>
        <p style={{
          fontFamily: 'var(--font-ticker)',
          fontSize: '20px',
          color: 'var(--sky)',
          opacity: 0.8,
          letterSpacing: '2px',
          textTransform: 'uppercase',
        }}>
          Agentic AI Pipeline • Multimodal Orchestration
        </p>
      </div>

      {/* Input Container */}
      <div className="glass" style={{
        padding: '32px',
        borderRadius: '24px',
        boxShadow: '0 20px 80px rgba(0,0,0,0.6)',
        border: `1px solid ${isTooShort ? 'rgba(255, 68, 68, 0.3)' : 'rgba(255,255,255,0.05)'}`,
        position: 'relative',
        zIndex: 10,
        transition: 'border-color 0.3s ease',
      }}>
        <textarea
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder="A neon-drenched cityscape where the rain falls upwards..."
          rows={4}
          disabled={disabled}
          style={{
            width: '100%',
            background: 'rgba(0,0,0,0.3)',
            border: `1px solid ${isTooShort ? '#ff4444' : focused ? 'var(--acid)' : 'rgba(255,255,255,0.1)'}`,
            borderRadius: '16px',
            fontFamily: 'var(--font-body)',
            fontSize: '18px',
            color: 'var(--snow)',
            padding: '24px',
            resize: 'none',
            outline: 'none',
            transition: 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
            boxShadow: focused ? '0 0 40px rgba(200,255,0,0.05)' : 'none',
            marginBottom: '8px',
          }}
        />
        
        {/* Validation hint */}
        <div style={{
          height: '24px',
          fontFamily: 'var(--font-ticker)',
          fontSize: '14px',
          color: isTooShort ? '#ff4444' : 'rgba(255,255,255,0.2)',
          marginBottom: '16px',
          paddingLeft: '8px',
          transition: 'color 0.3s ease',
        }}>
          {isTooShort ? '⚠️ PROMPT TOO SHORT (MIN 10 CHARS)' : prompt.length > 0 ? `${prompt.length}/500` : ''}
        </div>

        {/* Options Row */}
        <div style={{
          display: 'flex', gap: '32px', alignItems: 'center',
          marginBottom: '32px',
          flexWrap: 'wrap',
          background: 'rgba(255,255,255,0.03)',
          padding: '16px 24px',
          borderRadius: '12px',
        }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer', userSelect: 'none' }}>
            <input
              type="checkbox"
              checked={subtitles}
              onChange={e => setSubtitles(e.target.checked)}
              style={{
                accentColor: 'var(--acid)',
                width: '18px', height: '18px',
                cursor: 'pointer',
              }}
            />
            <span style={{ fontFamily: 'var(--font-ticker)', fontSize: '18px', color: 'var(--sky)' }}>
              BURN SUBTITLES
            </span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontFamily: 'var(--font-ticker)', fontSize: '18px', color: 'rgba(255,255,255,0.4)' }}>
              SEED_ID
            </span>
            <input
              type="number"
              value={seed}
              onChange={e => setSeed(e.target.value)}
              placeholder="RANDOM"
              style={{
                width: '100px',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '6px',
                color: 'var(--acid)',
                padding: '4px 12px',
                fontFamily: 'var(--font-ticker)',
                fontSize: '18px',
                outline: 'none',
              }}
            />
          </label>
        </div>

        {/* Submit Wrapper */}
        <div style={{ textAlign: 'center' }}>
          <ParticlesBurst trigger={submitted}>
            <button
              id="generate-btn"
              onClick={handleSubmit}
              disabled={!canSubmit}
              style={{
                padding: '20px 60px',
                fontSize: '24px',
                fontFamily: 'var(--font-display)',
                background: !canSubmit ? 'rgba(255,255,255,0.05)' : 'var(--acid)',
                color: !canSubmit ? 'rgba(255,255,255,0.2)' : 'var(--ink)',
                border: 'none',
                borderRadius: '12px',
                cursor: !canSubmit ? 'not-allowed' : 'pointer',
                transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
                boxShadow: !canSubmit ? 'none' : '0 10px 40px rgba(200,255,0,0.3)',
                textTransform: 'uppercase',
                letterSpacing: '1px',
              }}
              onMouseEnter={e => {
                if (canSubmit) {
                  e.target.style.transform = 'scale(1.05) translateY(-2px)'
                  e.target.style.boxShadow = '0 15px 50px rgba(200,255,0,0.4)'
                }
              }}
              onMouseLeave={e => {
                e.target.style.transform = 'scale(1) translateY(0)'
                e.target.style.boxShadow = !canSubmit ? 'none' : '0 10px 40px rgba(200,255,0,0.3)'
              }}
            >
              {disabled ? 'GENERATING...' : 'GENERATE FILM 🚀'}
            </button>
          </ParticlesBurst>
        </div>
      </div>

      {/* Decorative Orbs */}
      <div style={{
        position: 'absolute', top: '10%', left: '-10%',
        width: '300px', height: '300px',
        background: 'radial-gradient(circle, var(--grape) 0%, transparent 70%)',
        opacity: 0.1, zIndex: 0, pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', bottom: '0%', right: '-10%',
        width: '400px', height: '400px',
        background: 'radial-gradient(circle, var(--bubblegum) 0%, transparent 70%)',
        opacity: 0.1, zIndex: 0, pointerEvents: 'none',
      }} />
    </section>
  )
}
