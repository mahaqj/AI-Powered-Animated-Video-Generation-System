import PhaseCard from './PhaseCard'

export default function PipelineDashboard({ pipelineState, onRerun }) {
  const { phase1, phase2, phase3 } = pipelineState
  const doneCount = [phase1, phase2, phase3].filter(p => p.status === 'done').length

  return (
    <section style={{
      maxWidth: '900px',
      margin: '0 auto',
      padding: '0 24px 40px',
    }}>
      <h2 style={{
        fontFamily: 'var(--font-display)',
        fontSize: '32px',
        color: 'var(--snow)',
        marginBottom: '16px',
      }}>
        Pipeline Status
      </h2>

      {/* Master Progress */}
      <div style={{
        display: 'flex',
        gap: '8px',
        marginBottom: '24px',
        alignItems: 'center',
      }}>
        {[1, 2, 3].map(n => (
          <div key={n} style={{
            flex: 1,
            height: '10px',
            borderRadius: '5px',
            background: n <= doneCount ? 'var(--acid)' : 'var(--surface)',
            border: '1px solid var(--acid)',
            transition: 'background 0.4s ease',
          }} />
        ))}
        <span style={{
          fontFamily: 'var(--font-ticker)',
          fontSize: '18px',
          color: 'var(--acid)',
          minWidth: '48px',
          textAlign: 'right',
        }}>
          {doneCount}/3
        </span>
      </div>

      {/* Phase Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: '20px',
      }}>
        {[1, 2, 3].map((n, i) => {
          const phaseData = pipelineState[`phase${n}`]
          return (
            <div
              key={n}
              style={{
                animation: `fade-up 0.5s ease forwards`,
                animationDelay: `${i * 100}ms`,
                opacity: 0,
              }}
            >
              <PhaseCard
                phaseNumber={n}
                status={phaseData.status}
                data={phaseData.data}
                onRerun={() => onRerun(n)}
              />
            </div>
          )
        })}
      </div>
    </section>
  )
}
