import { useEffect, useRef, useState } from 'react'
import { PHASE_META } from '../utils/constants'
import StatusBadge from './StatusBadge'
import ProgressBar from './ProgressBar'

export default function PhaseCard({ phaseNumber, status = 'idle', data, onRerun }) {
  const meta = PHASE_META[phaseNumber]
  const [hovered, setHovered] = useState(false)
  const [popped, setPopped] = useState(false)
  const prevStatus = useRef(status)

  useEffect(() => {
    if (prevStatus.current !== 'done' && status === 'done') {
      setPopped(true)
      setTimeout(() => setPopped(false), 800)
    }
    prevStatus.current = status
  }, [status])

  const percent = status === 'done' ? 100 : status === 'running' ? 65 : 0
  const isRunning = status === 'running'
  const isDone = status === 'done'
  const isError = status === 'error'

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="glass"
      style={{
        borderRadius: '20px',
        padding: '24px',
        transition: 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
        transform: hovered ? 'translateY(-8px) scale(1.02)' : 'translateY(0) scale(1)',
        border: `1px solid ${hovered ? meta.color : 'rgba(255,255,255,0.08)'}`,
        boxShadow: hovered ? `0 20px 40px ${meta.color}15` : '0 10px 30px rgba(0,0,0,0.2)',
        animation: popped ? 'pop-scale 0.6s ease' : 'none',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Background glow on hover */}
      <div style={{
        position: 'absolute', top: '-50%', left: '-50%', width: '200%', height: '200%',
        background: `radial-gradient(circle, ${meta.color}05 0%, transparent 70%)`,
        opacity: hovered ? 1 : 0,
        transition: 'opacity 0.4s ease',
        pointerEvents: 'none',
      }} />

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', justifyContent: 'space-between', position: 'relative' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '44px', height: '44px',
            borderRadius: '12px',
            background: `${meta.color}15`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '24px',
            border: `1px solid ${meta.color}33`,
          }}>
            {meta.emoji}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontFamily: 'var(--font-ticker)', fontSize: '12px', color: 'rgba(255,255,255,0.4)', letterSpacing: '2px' }}>
              PHASE 0{phaseNumber}
            </span>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '22px', color: meta.color, lineHeight: 1 }}>
              {meta.name}
            </span>
          </div>
        </div>
        <StatusBadge status={status} />
      </div>

      {/* Progress */}
      <div style={{ position: 'relative' }}>
        <ProgressBar active={isRunning} percent={percent} color={meta.color} />
      </div>

      {/* Data Summary / Terminal Feed */}
      <div style={{
        fontFamily: 'var(--font-ticker)',
        fontSize: '15px',
        color: isDone ? 'var(--acid)' : 'rgba(255,255,255,0.4)',
        background: 'rgba(0,0,0,0.2)',
        padding: '12px',
        borderRadius: '10px',
        minHeight: '48px',
        display: 'flex',
        alignItems: 'center',
        border: `1px solid ${isDone ? 'var(--acid)22' : 'rgba(255,255,255,0.05)'}`,
      }}>
        {isDone && data ? (
          <div style={{ animation: 'curtain-wipe 0.5s ease forwards' }}>
            {phaseNumber === 1 && `> ${data.scene_count} SCENES GEN'D / ${data.characters?.length} CAST`}
            {phaseNumber === 2 && `> AUDIO CHANNELS SYNCED [OK]`}
            {phaseNumber === 3 && `> VIDEO RENDER COMPLETE`}
          </div>
        ) : isRunning ? (
          <span style={{ animation: 'pulse 1s infinite alternate' }}>[ PROCESSING... ]</span>
        ) : isError ? (
          <span style={{ color: '#ff4444' }}>[ ! ERROR DETECTED ]</span>
        ) : (
          <span>[ WAITING... ]</span>
        )}
      </div>

      {/* Actions */}
      {(isDone || isError) && (
        <button
          onClick={onRerun}
          style={{
            alignSelf: 'flex-start',
            border: '1px solid rgba(255,255,255,0.1)',
            color: 'rgba(255,255,255,0.6)',
            background: 'rgba(255,255,255,0.03)',
            fontFamily: 'var(--font-ticker)',
            fontSize: '14px',
            padding: '8px 18px',
            borderRadius: '8px',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            letterSpacing: '1px',
          }}
          onMouseEnter={e => {
            e.target.style.background = meta.color
            e.target.style.color = 'var(--ink)'
            e.target.style.borderColor = meta.color
          }}
          onMouseLeave={e => {
            e.target.style.background = 'rgba(255,255,255,0.03)'
            e.target.style.color = 'rgba(255,255,255,0.6)'
            e.target.style.borderColor = 'rgba(255,255,255,0.1)'
          }}
        >
          RE-RUN ENGINE
        </button>
      )}
    </div>
  )
}
