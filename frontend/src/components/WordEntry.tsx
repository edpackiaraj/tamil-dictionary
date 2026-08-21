import { useState } from 'react'
import { WordDetail, Contribution } from '../types'
import { apiVote, apiRequestWord } from '../api'

interface Props {
  word: WordDetail
  community: Contribution[]
  onBack: () => void
  onContribute: () => void
  onWordClick: (headword: string) => void
}

const FORM_TYPE_LABELS: Record<string, string> = {
  nominative_plural: 'Plural',
  locative: 'Locative (-இல்)',
  dative: 'Dative (-க்கு)',
  accusative: 'Accusative (-ஐ)',
  ablative: 'Ablative (-இல் இருந்து)',
  plural_locative: 'Plural Locative',
  genitive: 'Genitive (-இன்)',
  instrumental: 'Instrumental',
}

function Section({ title, icon, children, defaultOpen = true }: { title: string; icon: string; children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="section-card">
      <div className="section-header" onClick={() => setOpen(o => !o)} aria-expanded={open}>
        <div className="section-title">
          <span className="section-icon">{icon}</span>
          {title}
        </div>
        <span style={{ color: 'var(--color-text-3)', fontSize: '0.9rem' }}>{open ? '▲' : '▼'}</span>
      </div>
      {open && <div className="section-body">{children}</div>}
    </div>
  )
}

export default function WordEntry({ word, community, onBack, onContribute, onWordClick }: Props) {
  const [votedIds, setVotedIds] = useState<Set<string>>(new Set())

  const handleVote = async (id: string) => {
    if (votedIds.has(id)) return
    await apiVote(id, 'helpful')
    setVotedIds(prev => new Set(prev).add(id))
  }

  const statusLabel = word.lexical_status === 'published' ? 'published' : word.lexical_status

  return (
    <div className="word-entry">
      <button className="back-btn" onClick={onBack}>← தேடலுக்குத் திரும்பு</button>

      {/* ── Header ── */}
      <div className="word-header">
        <div className="word-header-top">
          <div>
            <div className="headword-tamil">{word.headword}</div>
            {word.transliteration && (
              <div className="headword-translit">
                {word.transliteration}
                {word.transliteration_iso && (
                  <span className="headword-translit-iso">· {word.transliteration_iso}</span>
                )}
              </div>
            )}
            {word.pronunciation_ipa && (
              <div style={{ fontSize: '0.85rem', color: 'var(--color-text-3)', marginTop: 4 }}>
                [{word.pronunciation_ipa}]
              </div>
            )}
            {word.pos_tamil && (
              <div className="pos-badge">
                <span className="ta">{word.pos_tamil}</span>
                {word.pos_english && <span style={{ color: 'var(--color-text-3)', fontSize: '0.78rem' }}>· {word.pos_english}</span>}
              </div>
            )}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
            <span className={`word-status ${statusLabel}`}>{statusLabel}</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-3)' }}>
              ID: {word.id} · Rev {word.revision}
            </span>
          </div>
        </div>

        {word.alternate_spellings?.length > 0 && (
          <div className="alternate-spellings">
            <span style={{ color: 'var(--color-text-3)' }}>மாற்று எழுத்துரு: </span>
            {word.alternate_spellings.join(' · ')}
          </div>
        )}

        <div className="word-actions">
          <button className="btn btn-primary" onClick={onContribute}>✏️ பங்களிப்பு சேர்க்க</button>
          <button className="btn btn-outline">🔊 உச்சரிப்பு</button>
          <button className="btn btn-outline">⬇️ பகிர்</button>
        </div>
      </div>

      {/* ── Senses ── */}
      <Section title="பொருள் — Meanings" icon="📖">
        {word.senses.map(sense => (
          <div className="sense-item" key={sense.id}>
            <div className="sense-top">
              <span className="sense-number">{sense.sense_number}</span>
              <div className="sense-defs">
                {sense.domain && <div className="sense-domain">{sense.domain}</div>}
                {sense.definitions_en.map((d, i) => (
                  <div key={i} className="sense-def-en">{d}</div>
                ))}
                {sense.definitions_ta.map((d, i) => (
                  <div key={i} className="sense-def-ta">{d}</div>
                ))}

                {sense.synonyms.length > 0 && (
                  <div style={{ marginTop: 10 }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-3)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>ஒத்த சொற்கள் </span>
                    <div className="word-chips">
                      {sense.synonyms.map(s => (
                        <button key={s} className="chip" onClick={() => onWordClick(s)}>{s}</button>
                      ))}
                    </div>
                  </div>
                )}

                {sense.antonyms.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-3)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>எதிர்ச்சொற்கள் </span>
                    <div className="word-chips">
                      {sense.antonyms.map(a => (
                        <button key={a} className="chip antonym" onClick={() => onWordClick(a)}>{a}</button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {sense.examples.length > 0 && (
              <div style={{ marginTop: 12, marginLeft: 38 }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--color-text-3)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>எடுத்துக்காட்டு</div>
                {sense.examples.map((ex, i) => (
                  <div key={i} className="example-item">
                    <div className="example-ta">{ex.tamil}</div>
                    {ex.english && <div className="example-en">{ex.english}</div>}
                  </div>
                ))}
              </div>
            )}

            {sense.quotations.length > 0 && (
              <div style={{ marginTop: 12, marginLeft: 38 }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--color-text-3)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>இலக்கிய மேற்கோள்</div>
                {sense.quotations.map((q, i) => (
                  <div key={i} className="quotation-item">
                    <div className="quotation-text">{q.text}</div>
                    <div className="quotation-source">
                      {q.source && <span>{q.source}</span>}
                      {q.chapter && <span> · {q.chapter}</span>}
                      {q.verse && <span> · {q.verse}</span>}
                      {q.century && <span> · {q.century}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {sense.sources.length > 0 && (
              <div style={{ marginTop: 12, marginLeft: 38 }}>
                {sense.sources.map((src, i) => (
                  <div key={i} className="source-item">
                    <span className="source-icon">📚</span>
                    <div>
                      <div className="source-title">{src.title}</div>
                      {src.page_ref && <div className="source-ref">p. {src.page_ref}</div>}
                      {src.quote && <div className="source-quote">"{src.quote}"</div>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </Section>

      {/* ── Morphology ── */}
      {word.morphological_forms.length > 0 && (
        <Section title="சொல் வடிவங்கள் — Word Forms" icon="🔄" defaultOpen={false}>
          <table className="morph-table">
            <thead>
              <tr>
                <th>வடிவம்</th>
                <th>வகை</th>
              </tr>
            </thead>
            <tbody>
              {word.morphological_forms.map((f, i) => (
                <tr key={i}>
                  <td>
                    <button className="chip" onClick={() => onWordClick(f.form)} style={{ border: 'none', background: 'transparent', padding: 0, fontSize: '1rem' }}>
                      {f.form}
                    </button>
                    {f.generated && <span className="morph-generated">auto</span>}
                  </td>
                  <td>{FORM_TYPE_LABELS[f.form_type] || f.form_type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      )}

      {/* ── Etymology ── */}
      {word.etymologies.length > 0 && (
        <Section title="சொற்பிறப்பியல் — Etymology" icon="🏺" defaultOpen={false}>
          {word.etymologies.map((e, i) => (
            <div key={i} style={{ marginBottom: 8 }}>
              {e.period && <span style={{ fontSize: '0.75rem', color: 'var(--color-text-3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{e.period} · </span>}
              <span style={{ color: 'var(--color-text-2)', fontSize: '0.9rem' }}>{e.etymology}</span>
            </div>
          ))}
        </Section>
      )}

      {/* ── Community ── */}
      <Section title={`சமூகக் குறிப்புகள் — Community Remarks (${community.length})`} icon="💬" defaultOpen={community.length > 0}>
        {community.length === 0 ? (
          <div style={{ color: 'var(--color-text-3)', fontSize: '0.9rem', textAlign: 'center', padding: '16px 0' }}>
            <div style={{ fontFamily: 'var(--font-tamil)', marginBottom: 8 }}>இன்னும் குறிப்புகள் இல்லை.</div>
            <button className="btn btn-outline" onClick={onContribute}>முதல் பங்களிப்பாளராக இருங்கள்</button>
          </div>
        ) : (
          <>
            {community.map(c => (
              <div key={c.id} className="contribution-card">
                <div className="community-badge">சமூகக் குறிப்பு</div>
                <div className="contribution-type">{c.type.replace('_', ' ')}</div>
                <div className="contribution-content">{c.content}</div>
                {c.explanation && (
                  <div style={{ fontSize: '0.85rem', color: 'var(--color-text-3)', marginTop: 6, fontFamily: 'var(--font-tamil)' }}>
                    {c.explanation}
                  </div>
                )}
                {c.example && (
                  <div className="example-item" style={{ marginTop: 8 }}>
                    <div className="example-ta">{c.example}</div>
                  </div>
                )}
                <div className="contribution-meta">
                  <span className="contribution-author">— {c.contributor}</span>
                  <span className="contribution-date">{new Date(c.submitted_at).toLocaleDateString('ta-IN')}</span>
                  {c.region && <span style={{ fontSize: '0.75rem', color: 'var(--color-purple)', background: 'rgba(167,139,250,0.12)', padding: '2px 8px', borderRadius: 99 }}>{c.region}</span>}
                  <button
                    className="contribution-vote"
                    onClick={() => handleVote(c.id)}
                    disabled={votedIds.has(c.id)}
                    style={votedIds.has(c.id) ? { color: 'var(--color-green)', borderColor: 'var(--color-green)' } : {}}
                  >
                    👍 பயனுள்ளது {c.helpful_count + (votedIds.has(c.id) ? 1 : 0)}
                  </button>
                </div>
              </div>
            ))}
          </>
        )}

        <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--color-border-soft)' }}>
          <button className="btn btn-primary" onClick={onContribute}>
            ✏️ உங்கள் அறிவைப் பகிருங்கள்
          </button>
          <p style={{ fontSize: '0.75rem', color: 'var(--color-text-3)', marginTop: 8 }}>
            Community contributions are reviewed by editors before being published.
            பங்களிப்புகள் ஆசிரியர் மதிப்பாய்வுக்குப் பின் வெளியிடப்படும்.
          </p>
        </div>
      </Section>

      {/* Footer */}
      <div style={{ textAlign: 'center', padding: '16px 0 8px', fontSize: '0.75rem', color: 'var(--color-text-3)' }}>
        தமிழ் அகராதி — Open Tamil Lexicon · {word.updated_at ? `Updated ${new Date(word.updated_at).toLocaleDateString()}` : ''}
      </div>
    </div>
  )
}
