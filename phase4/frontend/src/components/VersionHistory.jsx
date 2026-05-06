export default function VersionHistory({ history = [], onRevert }) {
  return (
    <section style={{
      maxWidth: '900px',
      margin: '0 auto',
      padding: '0 24px 60px',
    }}>
      <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '28px', color: 'var(--snow)', marginBottom: '16px' }}>
        ↩️ Version History
      </h2>

      {history.length === 0 ? (
        <p style={{ fontFamily: 'var(--font-ticker)', fontSize: '20px', color: '#555' }}>
          No versions yet — run the pipeline first
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {[...history].reverse().map((v, i) => {
            const isLatest = i === 0
            return (
              <div
                key={v.version || i}
                style={{
                  background: 'var(--surface)',
                  border: '1px solid #333',
                  borderLeft: `4px solid ${isLatest ? 'var(--acid)' : 'var(--grape)'}`,
                  borderRadius: '8px',
                  padding: '14px 18px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  opacity: isLatest ? 1 : 0.7,
                  flexWrap: 'wrap',
                  gap: '10px',
                }}
              >
                <div>
                  <span style={{ fontFamily: 'var(--font-ticker)', fontSize: '22px', color: isLatest ? 'var(--acid)' : 'var(--grape)' }}>
                    v{v.version || i + 1}
                  </span>
                  <span style={{ marginLeft: '12px', fontFamily: 'var(--font-body)', fontSize: '12px', color: '#888' }}>
                    {v.created_at ? new Date(v.created_at).toLocaleString() : 'Unknown time'}
                  </span>
                  <div style={{ fontFamily: 'var(--font-body)', fontSize: '12px', color: '#666', marginTop: '4px' }}>
                    {v.scene_count || '?'} scenes
                  </div>
                </div>

                {!isLatest && (
                  <button
                    onClick={() => onRevert(v.version || i + 1)}
                    style={{
                      fontFamily: 'var(--font-body)',
                      fontSize: '12px',
                      background: 'transparent',
                      border: '1px solid var(--grape)',
                      color: 'var(--grape)',
                      padding: '4px 12px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                    }}
                  >
                    Revert to v{v.version || i + 1}
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}
