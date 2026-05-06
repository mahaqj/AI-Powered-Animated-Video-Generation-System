import { AnimatePresence, motion } from 'framer-motion'

const TYPE_COLORS = { success: 'var(--acid)', error: '#ff4444', info: 'var(--sky)' }

function Toast({ id, message, type, onRemove }) {
  return (
    <motion.div
      key={id}
      initial={{ x: 120, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 120, opacity: 0, height: 0, marginBottom: 0 }}
      transition={{ duration: 0.25 }}
      onClick={() => onRemove(id)}
      style={{
        background: 'var(--surface)',
        borderLeft: `4px solid ${TYPE_COLORS[type] || TYPE_COLORS.info}`,
        borderRadius: '6px',
        padding: '12px 16px',
        fontFamily: 'var(--font-body)',
        fontSize: '13px',
        color: 'var(--snow)',
        maxWidth: '320px',
        cursor: 'pointer',
        marginBottom: '8px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
      }}
    >
      {message}
    </motion.div>
  )
}

export default function ToastNotifier({ toasts, onRemove }) {
  return (
    <div style={{
      position: 'fixed',
      bottom: '24px',
      right: '24px',
      zIndex: 9999,
      display: 'flex',
      flexDirection: 'column-reverse',
    }}>
      <AnimatePresence>
        {toasts.map(t => (
          <Toast key={t.id} {...t} onRemove={onRemove} />
        ))}
      </AnimatePresence>
    </div>
  )
}
