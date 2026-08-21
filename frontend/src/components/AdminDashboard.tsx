import { useState, useEffect } from 'react'

const BASE = (window as any).__TAMIL_DICT_API__ || 'http://localhost:8000'

interface QueueData {
  stats: { pending_contributions: number; open_reports: number; word_requests: number }
  zero_result_queries: Array<{ query: string; count: number }>
  contributions: Array<{
    id: string; word_id: string; type: string; content: string
    explanation?: string; region?: string; source_ref?: string
    submitted_at: string; helpful_count: number
  }>
}

async function fetchQueue(token: string): Promise<QueueData> {
  const r = await fetch(`${BASE}/admin/queue`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  if (r.status === 401) throw new Error('Unauthorized')
  return r.json()
}

async function reviewContribution(token: string, id: string, decision: string, note?: string) {
  const r = await fetch(`${BASE}/admin/review/${id}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, editor_note: note })
  })
  return r.json()
}

async function login(email: string, password: string): Promise<string> {
  const form = new FormData()
  form.append('username', email)
  form.append('password', password)
  const r = await fetch(`${BASE}/api/auth/login`, { method: 'POST', body: form })
  if (!r.ok) throw new Error('Login failed')
  const data = await r.json()
  if (data.role !== 'editor' && data.role !== 'admin') throw new Error('Not authorized as editor/admin')
  return data.access_token
}

/* ── Admin CSS ─────────────────────────────────────────────────────────── */
const adminStyles = `
  .admin-wrap { font-family: 'Inter', sans-serif; min-height: 100vh; background: #0f1117; color: #f0f2f8; }
  .admin-header { background: #181c27; border-bottom: 1px solid #2a2f42; padding: 16px 32px; display: flex; align-items: center; gap: 16px; }
  .admin-logo { font-size: 1.2rem; font-weight: 700; color: #4f9cf9; }
  .admin-subtitle { font-size: 0.8rem; color: #6b7390; }
  .admin-main { max-width: 1200px; margin: 0 auto; padding: 32px; }
  .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 32px; }
  .stat-card { background: #181c27; border: 1px solid #2a2f42; border-radius: 12px; padding: 20px; }
  .stat-number { font-size: 2rem; font-weight: 700; color: #4f9cf9; }
  .stat-label { font-size: 0.78rem; color: #6b7390; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.06em; }
  .section-title { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #6b7390; margin-bottom: 16px; }
  .contrib-card { background: #181c27; border: 1px solid #2a2f42; border-left: 3px solid #f5a623; border-radius: 10px; padding: 16px; margin-bottom: 12px; }
  .contrib-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
  .contrib-word { font-size: 1.1rem; font-weight: 600; color: #4f9cf9; font-family: 'Noto Sans Tamil', serif; }
  .contrib-type { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; color: #f5a623; background: rgba(245,166,35,0.12); padding: 3px 10px; border-radius: 99px; }
  .contrib-content { font-family: 'Noto Sans Tamil', serif; font-size: 1rem; color: #f0f2f8; line-height: 1.8; margin: 10px 0; }
  .contrib-meta { font-size: 0.78rem; color: #6b7390; }
  .actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
  .btn { display: inline-flex; align-items: center; gap: 5px; padding: 7px 14px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer; border: 1.5px solid transparent; transition: all 0.15s; font-family: 'Inter', sans-serif; }
  .btn-accept { background: rgba(76,175,130,0.15); border-color: #4caf82; color: #4caf82; }
  .btn-accept:hover { background: rgba(76,175,130,0.3); }
  .btn-reject { background: rgba(240,106,106,0.12); border-color: #f06a6a; color: #f06a6a; }
  .btn-reject:hover { background: rgba(240,106,106,0.25); }
  .btn-evidence { background: rgba(79,156,249,0.12); border-color: #4f9cf9; color: #4f9cf9; }
  .btn-evidence:hover { background: rgba(79,156,249,0.25); }
  .btn-muted { background: transparent; border-color: #2a2f42; color: #6b7390; }
  .btn-primary { background: #4f9cf9; border-color: #4f9cf9; color: #fff; }
  .btn-primary:hover { filter: brightness(1.1); }
  .note-input { width: 100%; background: #1e2333; border: 1px solid #2a2f42; border-radius: 6px; padding: 8px 12px; color: #f0f2f8; font-size: 0.88rem; outline: none; margin: 8px 0; font-family: 'Inter', sans-serif; }
  .note-input:focus { border-color: #4f9cf9; }
  .zero-chip { display: inline-flex; align-items: center; gap: 6px; background: #1e2333; border: 1px solid #2a2f42; border-radius: 99px; padding: 4px 12px; font-size: 0.82rem; color: #9ba3be; margin: 4px; }
  .zero-count { background: #f06a6a; color: #fff; border-radius: 99px; padding: 0 6px; font-size: 0.72rem; font-weight: 700; }
  .done-badge { font-size: 0.75rem; color: #4caf82; font-weight: 600; }
  .login-wrap { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #0f1117; }
  .login-card { background: #181c27; border: 1px solid #2a2f42; border-radius: 16px; padding: 40px 36px; width: 340px; }
  .login-title { font-size: 1.3rem; font-weight: 700; color: #f0f2f8; margin-bottom: 6px; }
  .login-sub { font-size: 0.85rem; color: #6b7390; margin-bottom: 28px; }
  .form-label { display: block; font-size: 0.75rem; font-weight: 600; color: #9ba3be; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
  .form-input { width: 100%; background: #1e2333; border: 1.5px solid #2a2f42; border-radius: 8px; padding: 10px 14px; color: #f0f2f8; font-size: 0.95rem; outline: none; margin-bottom: 14px; font-family: 'Inter', sans-serif; }
  .form-input:focus { border-color: #4f9cf9; }
  .err-msg { background: rgba(240,106,106,0.1); border: 1px solid #f06a6a; border-radius: 8px; padding: 10px 14px; color: #f06a6a; font-size: 0.85rem; margin-bottom: 12px; }
`

export default function AdminDashboard() {
  const [token, setToken]     = useState<string | null>(localStorage.getItem('admin_token'))
  const [data, setData]       = useState<QueueData | null>(null)
  const [loading, setLoading] = useState(false)
  const [reviewed, setReviewed] = useState<Set<string>>(new Set())
  const [notes, setNotes]     = useState<Record<string, string>>({})
  const [email, setEmail]     = useState('')
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [activeTab, setActiveTab] = useState<'queue' | 'zero_results'>('queue')

  const loadData = async (t: string) => {
    setLoading(true)
    try {
      const d = await fetchQueue(t)
      setData(d)
    } catch (e: any) {
      if (e.message === 'Unauthorized') { localStorage.removeItem('admin_token'); setToken(null) }
    } finally { setLoading(false) }
  }

  useEffect(() => { if (token) loadData(token) }, [token])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault(); setLoginError('')
    try {
      const t = await login(email, password)
      localStorage.setItem('admin_token', t)
      setToken(t)
    } catch (err: any) { setLoginError(err.message) }
  }

  const handleReview = async (id: string, decision: string) => {
    if (!token) return
    await reviewContribution(token, id, decision, notes[id])
    setReviewed(prev => new Set(prev).add(id))
  }

  if (!token) return (
    <div className="login-wrap">
      <style>{adminStyles}</style>
      <div className="login-card">
        <div className="login-title">📚 Editor Login</div>
        <div className="login-sub">Tamil Dictionary — Editorial Dashboard</div>
        {loginError && <div className="err-msg">{loginError}</div>}
        <form onSubmit={handleLogin}>
          <label className="form-label">Email</label>
          <input className="form-input" type="email" value={email} onChange={e => setEmail(e.target.value)} required autoFocus />
          <label className="form-label">Password</label>
          <input className="form-input" type="password" value={password} onChange={e => setPassword(e.target.value)} required />
          <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', padding: '11px' }}>
            உள்நுழை — Sign In
          </button>
        </form>
      </div>
    </div>
  )

  return (
    <>
      <style>{adminStyles}</style>
      <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@400;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
      <div className="admin-wrap">
        {/* Header */}
        <div className="admin-header">
          <div>
            <div className="admin-logo">📚 Tamil Dictionary</div>
            <div className="admin-subtitle">Editorial Dashboard — ஆசிரியர் பணியிடம்</div>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <button className="btn btn-muted" onClick={() => loadData(token!)}>🔄 Refresh</button>
            <button className="btn btn-muted" onClick={() => { localStorage.removeItem('admin_token'); setToken(null) }}>Sign Out</button>
          </div>
        </div>

        <div className="admin-main">
          {loading && <div style={{ color: '#6b7390', textAlign: 'center', padding: 40 }}>⏳ Loading queue…</div>}

          {data && (
            <>
              {/* Stats */}
              <div className="stat-grid">
                <div className="stat-card">
                  <div className="stat-number" style={{ color: '#f5a623' }}>{data.stats.pending_contributions}</div>
                  <div className="stat-label">Pending Contributions</div>
                </div>
                <div className="stat-card">
                  <div className="stat-number" style={{ color: '#f06a6a' }}>{data.stats.open_reports}</div>
                  <div className="stat-label">Open Reports</div>
                </div>
                <div className="stat-card">
                  <div className="stat-number" style={{ color: '#a78bfa' }}>{data.stats.word_requests}</div>
                  <div className="stat-label">Word Requests</div>
                </div>
                <div className="stat-card">
                  <div className="stat-number" style={{ color: '#4caf82' }}>{reviewed.size}</div>
                  <div className="stat-label">Reviewed (this session)</div>
                </div>
              </div>

              {/* Tabs */}
              <div style={{ display: 'flex', gap: 4, marginBottom: 24 }}>
                {([['queue', '📋 Contributions'], ['zero_results', '🔍 Zero Results']] as const).map(([tab, label]) => (
                  <button
                    key={tab}
                    className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-muted'}`}
                    onClick={() => setActiveTab(tab)}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {/* Contribution Queue */}
              {activeTab === 'queue' && (
                <div>
                  <div className="section-title">📋 Pending Contributions — மதிப்பாய்வு வரிசை</div>
                  {data.contributions.length === 0 && (
                    <div style={{ color: '#6b7390', textAlign: 'center', padding: '40px 0' }}>
                      ✅ வரிசை காலியாக உள்ளது — Queue is empty
                    </div>
                  )}
                  {data.contributions.map(c => (
                    <div className="contrib-card" key={c.id} style={reviewed.has(c.id) ? { opacity: 0.5 } : {}}>
                      <div className="contrib-header">
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                            {c.word_id && <span className="contrib-word">{c.word_id}</span>}
                            <span className="contrib-type">{c.type.replace('_', ' ')}</span>
                            {reviewed.has(c.id) && <span className="done-badge">✓ Reviewed</span>}
                          </div>
                          <div className="contrib-meta" style={{ marginTop: 4 }}>
                            {new Date(c.submitted_at).toLocaleDateString()} · 👍 {c.helpful_count}
                            {c.region && ` · 📍 ${c.region}`}
                          </div>
                        </div>
                      </div>

                      <div className="contrib-content">{c.content}</div>

                      {c.explanation && (
                        <div style={{ fontSize: '0.85rem', color: '#9ba3be', fontStyle: 'italic', marginBottom: 8 }}>
                          💬 {c.explanation}
                        </div>
                      )}
                      {c.source_ref && (
                        <div style={{ fontSize: '0.82rem', color: '#6b7390', marginBottom: 8 }}>
                          📚 Source: {c.source_ref}
                        </div>
                      )}

                      {!reviewed.has(c.id) && (
                        <>
                          <input
                            className="note-input"
                            placeholder="Editor note (optional)…"
                            value={notes[c.id] || ''}
                            onChange={e => setNotes(n => ({ ...n, [c.id]: e.target.value }))}
                          />
                          <div className="actions">
                            <button className="btn btn-accept" onClick={() => handleReview(c.id, 'accept')}>
                              ✅ Accept & Publish
                            </button>
                            <button className="btn btn-evidence" onClick={() => handleReview(c.id, 'request_evidence')}>
                              🔍 Request Evidence
                            </button>
                            <button className="btn btn-reject" onClick={() => handleReview(c.id, 'reject')}>
                              ✕ Reject
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Zero Results */}
              {activeTab === 'zero_results' && (
                <div>
                  <div className="section-title">
                    🔍 Zero-Result Searches — இல்லாத சொல் தேடல்கள்
                  </div>
                  <p style={{ fontSize: '0.85rem', color: '#6b7390', marginBottom: 16, lineHeight: 1.6 }}>
                    These words were searched but not found. Use them to prioritize new dictionary entries.
                  </p>
                  <div>
                    {data.zero_result_queries.map(z => (
                      <span key={z.query} className="zero-chip">
                        <span style={{ fontFamily: 'Noto Sans Tamil, serif' }}>{z.query}</span>
                        <span className="zero-count">{z.count}</span>
                      </span>
                    ))}
                  </div>
                  {data.zero_result_queries.length === 0 && (
                    <div style={{ color: '#6b7390', padding: '20px 0' }}>
                      No zero-result searches recorded yet.
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  )
}
