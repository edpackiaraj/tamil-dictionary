import { useState, useEffect } from 'react'
import SearchBar from './components/SearchBar'
import WordEntry from './components/WordEntry'
import ContributionForm from './components/ContributionForm'
import AdminDashboard from './components/AdminDashboard'
import { WordDetail, Contribution, View } from './types'
import { apiGetWord, apiGetCommunity, apiSearch } from './api'


export default function App() {
  // Route to admin dashboard
  if (window.location.pathname.includes('/admin') || window.location.hash === '#/admin') {
    return <AdminDashboard />
  }

  const [view, setView]       = useState<View>('search')

  const [word, setWord]       = useState<WordDetail | null>(null)
  const [community, setCommunity] = useState<Contribution[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  const loadWord = async (id: string) => {
    setLoading(true); setError('')
    try {
      const w = await apiGetWord(id)
      const c = await apiGetCommunity(id)
      setWord(w)
      setCommunity(c)
      setView('word')
    } catch (e: any) {
      setError(e.message || 'Word not found')
    } finally {
      setLoading(false)
    }
  }

  const handleWordClick = async (headword: string) => {
    // Search for the headword and open first result
    try {
      const res = await apiSearch(headword)
      if (res.results?.length > 0) loadWord(res.results[0].id)
    } catch {}
  }

  return (
    <div className="dict-widget">
      <SearchBar onSelect={loadWord} />

      {loading && (
        <div className="loading">
          <div className="spinner" />
          <span className="ta">தேடுகிறது…</span>
        </div>
      )}

      {error && !loading && (
        <div className="zero-result">
          <div className="zero-result-icon">🔍</div>
          <div className="zero-result-title">இந்தச் சொல் அகராதியில் இல்லை</div>
          <div className="zero-result-subtitle">This word was not found in the dictionary.</div>
          <button
            className="btn btn-primary"
            onClick={async () => {
              // request the word
              setError('')
            }}
          >
            இந்தச் சொல்லை சேர்க்கப் பரிந்துரைக்கவும்
          </button>
        </div>
      )}

      {!loading && !error && view === 'word' && word && (
        <WordEntry
          word={word}
          community={community}
          onBack={() => setView('search')}
          onContribute={() => setView('contribute')}
          onWordClick={handleWordClick}
        />
      )}

      {!loading && view === 'contribute' && word && (
        <ContributionForm
          wordId={word.id}
          headword={word.headword}
          onBack={() => setView('word')}
        />
      )}

      {!loading && view === 'search' && (
        <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--color-text-3)' }}>
          <div style={{ fontSize: '3rem', marginBottom: 16 }}>📚</div>
          <div className="ta" style={{ fontSize: '1.4rem', color: 'var(--color-text-2)', marginBottom: 8, fontWeight: 600 }}>
            தமிழ் அகராதி
          </div>
          <div style={{ fontSize: '1rem', color: 'var(--color-text-2)', marginBottom: 4 }}>Open Tamil Lexicon</div>
          <div style={{ fontSize: '0.85rem', maxWidth: 400, margin: '12px auto', lineHeight: 1.7 }}>
            Community-maintained • Editorially reviewed • Open source<br/>
            <span className="ta">சமூகத்தால் பராமரிக்கப்படுகிறது • ஆசிரியர் மதிப்பாய்வு செய்யப்படுகிறது</span>
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap', marginTop: 20 }}>
            {['அன்பு', 'கடல்', 'பால்', 'வீடு', 'அறம்'].map(w => (
              <button key={w} className="chip" style={{ fontSize: '1rem', padding: '6px 16px' }} onClick={() => handleWordClick(w)}>
                {w}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
