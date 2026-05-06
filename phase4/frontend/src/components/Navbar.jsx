import { STATUS_COLORS } from '../utils/constants'

export default function Navbar({ status = 'idle' }) {
  const isRunning = status === 'running'
  const isDone    = status === 'done'

  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 1000,
      height: '64px',
      background: 'rgba(8,8,16,0.85)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      borderBottom: '1px solid rgba(200,255,0,0.2)',
      boxShadow: '0 4px 40px rgba(0,0,0,0.5)',
      display: 'flex', alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 32px',
    }}>
      {/* Logo */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '10px',
      }}>
        <span style={{
          fontFamily: 'var(--font-display)',
          fontSize: '30px',
          background: 'linear-gradient(135deg, var(--acid) 0%, var(--sky) 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          letterSpacing: '1px',
          filter: 'drop-shadow(0 0 12px rgba(200,255,0,0.4))',
        }}>
          AnimAI
        </span>
        <span style={{ fontSize: '20px' }}>🎬</span>
        <span style={{
          fontFamily: 'var(--font-ticker)',
          fontSize: '13px',
          color: 'rgba(255,255,255,0.25)',
          borderLeft: '1px solid rgba(255,255,255,0.1)',
          paddingLeft: '10px',
          letterSpacing: '2px',
        }}>
          PHASE 4
        </span>
      </div>

      {/* Right side */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Status pill */}
        <div style={{
          fontFamily: 'var(--font-ticker)',
          fontSize: '15px',
          padding: '5px 16px',
          borderRadius: '999px',
          background: (STATUS_COLORS[status] || '#888') + '18',
          border: `1px solid ${STATUS_COLORS[status] || '#888'}55`,
          color: STATUS_COLORS[status] || '#888',
          textTransform: 'uppercase',
          letterSpacing: '1.5px',
          animation: isRunning ? 'pulse 1.2s ease infinite alternate' : 'none',
          display: 'flex', alignItems: 'center', gap: '6px',
        }}>
          <span style={{
            width: '6px', height: '6px',
            borderRadius: '50%',
            background: STATUS_COLORS[status] || '#888',
            display: 'inline-block',
            boxShadow: `0 0 8px ${STATUS_COLORS[status] || '#888'}`,
            animation: isRunning ? 'pulse 0.8s ease infinite alternate' : 'none',
          }} />
          {status}
        </div>

        {/* API indicator */}
        <div style={{
          fontFamily: 'var(--font-ticker)',
          fontSize: '13px',
          color: 'rgba(255,255,255,0.3)',
          borderLeft: '1px solid rgba(255,255,255,0.1)',
          paddingLeft: '12px',
          letterSpacing: '1px',
        }}>
          :8002
        </div>
      </div>
    </nav>
  )
}
