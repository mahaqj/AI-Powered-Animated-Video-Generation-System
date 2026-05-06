export default function ProgressBar({ active = false, percent = 0, color = 'var(--acid)' }) {
  return (
    <div style={{
      height: '6px',
      borderRadius: '3px',
      background: 'rgba(255,255,255,0.03)',
      border: '1px solid rgba(255,255,255,0.05)',
      overflow: 'hidden',
      position: 'relative',
    }}>
      <div style={{
        height: '100%',
        width: `${Math.min(100, Math.max(0, percent))}%`,
        background: `linear-gradient(90deg, ${color}, var(--sky), ${color})`,
        backgroundSize: '200% auto',
        borderRadius: '3px',
        transition: 'width 0.6s cubic-bezier(0.16, 1, 0.3, 1)',
        animation: active ? 'shimmer 2s linear infinite' : 'none',
        boxShadow: `0 0 10px ${color}55`,
      }} />
      
      {/* Gloss overlay */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '40%',
        background: 'rgba(255,255,255,0.05)',
        pointerEvents: 'none',
      }} />
    </div>
  )
}
