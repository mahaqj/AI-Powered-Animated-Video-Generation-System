export default function VideoPreview({ videoUrl, onRegenerate }) {
  const placeholder = (
    <div style={{
      width: '100%',
      maxWidth: '900px',
      minHeight: '280px',
      border: '2px dashed var(--grape)',
      borderRadius: '12px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexDirection: 'column',
      gap: '12px',
      background: `repeating-linear-gradient(
        90deg,
        var(--surface) 0px,
        var(--surface) 20px,
        #1a1a2e 20px,
        #1a1a2e 22px
      )`,
    }}>
      <span style={{ fontFamily: 'var(--font-ticker)', fontSize: '28px', color: 'var(--grape)' }}>
        🎞️ Your film will appear here
      </span>
      <span style={{ fontFamily: 'var(--font-body)', fontSize: '12px', color: '#555' }}>
        Submit a prompt above to begin generation
      </span>
    </div>
  )

  const player = (
    <div style={{
      animation: 'curtain-wipe 0.8s ease forwards',
      clipPath: 'inset(0 100% 0 0)',
    }}>
      <video
        controls
        autoPlay
        loop
        src={videoUrl}
        style={{
          width: '100%',
          maxWidth: '900px',
          borderRadius: '12px',
          border: '3px solid var(--acid)',
          boxShadow: '8px 8px 0px var(--bubblegum)',
          display: 'block',
        }}
      />
      <div style={{ display: 'flex', gap: '12px', marginTop: '16px', flexWrap: 'wrap' }}>
        <a
          href={videoUrl}
          download="animai_film.mp4"
          style={{
            padding: '10px 24px',
            fontFamily: 'var(--font-display)',
            fontSize: '16px',
            background: 'var(--sky)',
            color: 'var(--ink)',
            borderRadius: '6px',
            boxShadow: '3px 3px 0px var(--grape)',
            transition: 'all 0.2s ease',
            display: 'inline-block',
          }}
        >
          ⬇ Download
        </a>
        {onRegenerate && (
          <button
            onClick={onRegenerate}
            style={{
              padding: '10px 24px',
              fontFamily: 'var(--font-display)',
              fontSize: '16px',
              background: 'transparent',
              color: 'var(--mango)',
              border: '2px solid var(--mango)',
              borderRadius: '6px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            ↺ Regenerate All
          </button>
        )}
      </div>
    </div>
  )

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
        marginBottom: '20px',
      }}>
        Your Film 🎬
      </h2>
      {videoUrl ? player : placeholder}
    </section>
  )
}
