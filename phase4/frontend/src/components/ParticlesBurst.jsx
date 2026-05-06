import { useEffect, useState } from 'react'
import { PARTICLE_EMOJIS } from '../utils/constants'

function Particle({ emoji, x, delay, duration }) {
  return (
    <span style={{
      position: 'absolute',
      left: `calc(50% + ${x}px)`,
      bottom: '0',
      fontSize: '20px',
      pointerEvents: 'none',
      animation: `float-up ${duration}s ease forwards`,
      animationDelay: `${delay}s`,
      userSelect: 'none',
    }}>
      {emoji}
    </span>
  )
}

export default function ParticlesBurst({ trigger, children }) {
  const [particles, setParticles] = useState([])

  useEffect(() => {
    if (!trigger) return
    const newParticles = Array.from({ length: 8 }, (_, i) => ({
      id: Date.now() + i,
      emoji: PARTICLE_EMOJIS[Math.floor(Math.random() * PARTICLE_EMOJIS.length)],
      x: Math.random() * 120 - 60,
      delay: Math.random() * 0.3,
      duration: 0.8 + Math.random() * 0.6,
    }))
    setParticles(newParticles)
    setTimeout(() => setParticles([]), 1600)
  }, [trigger])

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      {particles.map(p => <Particle key={p.id} {...p} />)}
      {children}
    </div>
  )
}
