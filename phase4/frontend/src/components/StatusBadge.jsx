import { STATUS_COLORS } from '../utils/constants'

export default function StatusBadge({ status = 'idle' }) {
  const color = STATUS_COLORS[status] || STATUS_COLORS.idle
  return (
    <span style={{
      fontFamily: 'var(--font-ticker)',
      fontSize: '14px',
      padding: '2px 10px',
      borderRadius: '999px',
      background: color + '22',
      border: `1px solid ${color}`,
      color,
      textTransform: 'uppercase',
      letterSpacing: '1px',
      whiteSpace: 'nowrap',
    }}>
      {status === 'running' && (
        <span style={{ animation: 'pulse 0.8s ease infinite alternate', marginRight: '4px' }}>●</span>
      )}
      {status}
    </span>
  )
}
