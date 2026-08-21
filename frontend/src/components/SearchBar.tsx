import React, { useState, useRef, useEffect, useCallback } from 'react'
import { apiSearch } from '../api'
import { SearchResult } from '../types'

interface Props {
  onSelect: (id: string) => void
}

export default function SearchBar({ onSelect }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout>>()
  const inputRef = useRef<HTMLInputElement>(null)

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim()) { setResults([]); return }
    setLoading(true)
    try {
      const data = await apiSearch(q)
      setResults(data.results || [])
      setShowDropdown(true)
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    clearTimeout(timer.current)
    if (query.trim().length < 1) { setResults([]); setShowDropdown(false); return }
    timer.current = setTimeout(() => doSearch(query), 280)
    return () => clearTimeout(timer.current)
  }, [query, doSearch])

  const handleSelect = (id: string) => {
    setShowDropdown(false)
    onSelect(id)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && results.length > 0) handleSelect(results[0].id)
  }

  return (
    <div className="search-wrapper">
      <div className="search-box">
        <span className="search-icon">🔍</span>
        <input
          ref={inputRef}
          className="search-input"
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => results.length > 0 && setShowDropdown(true)}
          placeholder="சொல் தேடுக… or search in English"
          aria-label="Search Tamil dictionary"
          autoComplete="off"
        />
        {loading && <div className="spinner" style={{ width: 18, height: 18, flexShrink: 0 }} />}
        {query && !loading && (
          <button className="search-clear" onClick={() => { setQuery(''); setResults([]); setShowDropdown(false); inputRef.current?.focus() }} aria-label="Clear search">✕</button>
        )}
      </div>

      <div className="search-hint">
        <span>🔤 Tamil script</span>
        <span>🔡 English</span>
        <span>🔀 Transliteration</span>
      </div>

      {showDropdown && results.length > 0 && (
        <div style={{ marginTop: 8, border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', overflow: 'hidden', boxShadow: 'var(--shadow-card)' }}>
          {results.slice(0, 8).map(r => (
            <div
              key={r.id}
              className="result-item"
              style={{ borderRadius: 0, borderLeft: 'none', borderRight: 'none', borderTop: 'none' }}
              onClick={() => handleSelect(r.id)}
              role="button"
              tabIndex={0}
              onKeyDown={e => e.key === 'Enter' && handleSelect(r.id)}
            >
              <div>
                <div className="result-headword ta">{r.headword}</div>
                {r.transliteration && <div className="result-translit">{r.transliteration}</div>}
                {r.pos_tamil && <div className="result-pos ta">{r.pos_tamil}</div>}
              </div>
              <div className="result-def">{r.first_english_def || r.first_tamil_def}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
