// const BASE = '/api'

// async function fetchJSON(path, opts = {}) {
//   const res = await fetch(BASE + path, {
//     headers: { 'Content-Type': 'application/json', ...opts.headers },
//     ...opts,
//   })
//   if (!res.ok) {
//     const text = await res.text()
//     throw new Error(`HTTP ${res.status}: ${text}`)
//   }
//   return res.json()
// }

// export async function runPipeline(prompt, addSubtitles = false, seed = null) {
//   return fetchJSON('/pipeline/run', {
//     method: 'POST',
//     body: JSON.stringify({ prompt, add_subtitles: addSubtitles, seed }),
//   })
// }

// export async function rerunPhase(runId, phase) {
//   return fetchJSON('/pipeline/rerun', {
//     method: 'POST',
//     body: JSON.stringify({ run_id: runId, phase }),
//   })
// }

// export async function fetchPhase3State() {
//   return fetchJSON('/phase3/state')
// }

// export async function fetchHistory() {
//   return fetchJSON('/phase3/history')
// }

// export async function revertVersion(version) {
//   return fetchJSON(`/phase3/revert/${version}`, { method: 'POST' })
// }

// export async function fetchHealth() {
//   return fetchJSON('/health')
// }

// export function getVideoUrl(runId) {
//   return runId ? `/api/video/${runId}` : null
// }
const BASE = '/api'

async function fetchJSON(path, opts = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`HTTP ${res.status}: ${text}`)
  }

  return res.json()
}

export async function runPipeline(prompt, addSubtitles = false, seed = null) {
  return fetchJSON('/pipeline/run', {
    method: 'POST',
    body: JSON.stringify({ prompt, add_subtitles: addSubtitles, seed }),
  })
}

export async function rerunPhase(runId, phase) {
  return fetchJSON('/pipeline/rerun', {
    method: 'POST',
    body: JSON.stringify({ run_id: runId, phase }),
  })
}

export async function fetchPhase3State() {
  return fetchJSON('/phase3/state')
}

export async function fetchHistory(runDir) {
  return fetchJSON('/phase5/history', {
    method: 'POST',
    body: JSON.stringify({ run_dir: runDir }),
  })
}

export async function revertVersion(runDir, versionId) {
  return fetchJSON('/phase5/revert', {
    method: 'POST',
    body: JSON.stringify({
      run_dir: runDir,
      version_id: versionId,
    }),
  })
}

export async function fetchHealth() {
  return fetchJSON('/health')
}

export function getVideoUrl(runId) {
  return runId ? `/api/video/${runId}` : null
}