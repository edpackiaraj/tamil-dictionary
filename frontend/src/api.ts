const BASE = import.meta.env.VITE_API_BASE || 'https://tamil-dictionary-production.up.railway.app'

export async function apiSearch(q: string): Promise<any> {
  const r = await fetch(`${BASE}/api/search?q=${encodeURIComponent(q)}&limit=30`)
  if (!r.ok) throw new Error('Search failed')
  return r.json()
}

export async function apiGetWord(id: string): Promise<any> {
  const r = await fetch(`${BASE}/api/words/${encodeURIComponent(id)}`)
  if (!r.ok) throw new Error('Word not found')
  return r.json()
}

export async function apiGetCommunity(wordId: string): Promise<any[]> {
  const r = await fetch(`${BASE}/api/words/${encodeURIComponent(wordId)}/community`)
  if (!r.ok) return []
  return r.json()
}

export async function apiSubmitContribution(body: object): Promise<any> {
  const r = await fetch(`${BASE}/api/contribute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) {
    const err = await r.json()
    throw new Error(err.detail || 'Submission failed')
  }
  return r.json()
}

export async function apiVote(contribution_id: string, vote: string): Promise<void> {
  await fetch(`${BASE}/api/vote`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ contribution_id, vote }),
  })
}

export async function apiRequestWord(word: string, suggested_meaning?: string): Promise<any> {
  const r = await fetch(`${BASE}/api/request-word`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ word, suggested_meaning }),
  })
  return r.json()
}
