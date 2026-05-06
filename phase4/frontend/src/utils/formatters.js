export function msToReadable(ms) {
  const totalSeconds = Math.floor(ms / 1000)
  const m = Math.floor(totalSeconds / 60)
  const s = totalSeconds % 60
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}

export function bytesToMB(bytes) {
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

export function truncatePrompt(text, max = 60) {
  if (!text) return ''
  return text.length > max ? text.slice(0, max) + '…' : text
}
