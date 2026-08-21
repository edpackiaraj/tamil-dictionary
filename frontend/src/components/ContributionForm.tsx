import { useState } from 'react'
import { apiSubmitContribution } from '../api'

interface Props {
  wordId: string
  headword: string
  onBack: () => void
}

const TYPES = [
  { value: 'additional_meaning', label: 'கூடுதல் பொருள் — Additional Meaning' },
  { value: 'regional_meaning',   label: 'வட்டார வழக்கு — Regional Usage' },
  { value: 'modern_usage',       label: 'நவீனப் பயன்பாடு — Modern Usage' },
  { value: 'correction',         label: 'திருத்தம் — Correction' },
  { value: 'example',            label: 'எடுத்துக்காட்டு — Example Sentence' },
  { value: 'pronunciation',      label: 'உச்சரிப்பு — Pronunciation Note' },
  { value: 'translation',        label: 'மொழிபெயர்ப்பு — Translation' },
  { value: 'source',             label: 'ஆதாரம் — Source / Reference' },
  { value: 'spelling',           label: 'எழுத்துரு — Spelling Variant' },
  { value: 'other',              label: 'மற்றவை — Other' },
]

export default function ContributionForm({ wordId, headword, onBack }: Props) {
  const [type, setType]       = useState('additional_meaning')
  const [content, setContent] = useState('')
  const [explanation, setExplanation] = useState('')
  const [example, setExample] = useState('')
  const [region, setRegion]   = useState('')
  const [source, setSource]   = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError]     = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!content.trim()) { setError('உங்கள் பங்களிப்பை உள்ளிடவும்.'); return }
    setLoading(true); setError('')
    try {
      await apiSubmitContribution({
        word_id: wordId,
        type, content, explanation,
        example: example || undefined,
        region: region || undefined,
        source_ref: source || undefined,
      })
      setSuccess(true)
    } catch (err: any) {
      setError(err.message || 'பங்களிப்பு சமர்ப்பிக்க முடியவில்லை.')
    } finally {
      setLoading(false)
    }
  }

  if (success) return (
    <div>
      <button className="back-btn" onClick={onBack}>← திரும்பு</button>
      <div className="form-card">
        <div className="form-success">
          ✅ உங்கள் பங்களிப்பு பெறப்பட்டது!<br />
          ஆசிரியர் மதிப்பாய்வுக்குப் பிறகு "{headword}" பக்கத்தில் வெளியிடப்படும்.<br />
          நன்றி!
        </div>
        <div style={{ marginTop: 16 }}>
          <button className="btn btn-outline" onClick={onBack}>அகராதிக்கு திரும்பு</button>
        </div>
      </div>
    </div>
  )

  return (
    <div>
      <button className="back-btn" onClick={onBack}>← "{headword}" க்கு திரும்பு</button>
      <div className="form-card">
        <div className="form-title">
          ✏️ பங்களிப்பு சேர்க்க — Contribute to "{headword}"
        </div>

        <div style={{ background: 'rgba(245,166,35,0.08)', border: '1px solid rgba(245,166,35,0.2)', borderRadius: 8, padding: '10px 14px', marginBottom: 16, fontSize: '0.82rem', color: 'var(--color-text-3)' }}>
          📋 உங்கள் பங்களிப்பு ஆசிரியர் மதிப்பாய்வுக்குப் பிறகு மட்டுமே வெளியிடப்படும்.
          Community contributions are reviewed before publication.
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">பங்களிப்பு வகை — Type *</label>
            <select className="form-select" value={type} onChange={e => setType(e.target.value)}>
              {TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">உங்கள் பங்களிப்பு — Contribution *</label>
            <textarea
              className="form-textarea"
              value={content}
              onChange={e => setContent(e.target.value)}
              placeholder="இங்கே தமிழில் உள்ளிடவும்…"
              required
              rows={4}
            />
          </div>

          <div className="form-group">
            <label className="form-label">விளக்கம் — Explanation</label>
            <textarea
              className="form-textarea"
              value={explanation}
              onChange={e => setExplanation(e.target.value)}
              placeholder="ஏன் இந்தப் பொருள்? ஆதாரம் என்ன?"
              rows={2}
            />
          </div>

          <button
            type="button"
            className="form-advanced-toggle"
            onClick={() => setShowAdvanced(v => !v)}
          >
            {showAdvanced ? '▲' : '▼'} கூடுதல் தகவல் — Advanced fields
          </button>

          {showAdvanced && (
            <>
              <div className="form-group">
                <label className="form-label">எடுத்துக்காட்டு வாக்கியம் — Example sentence</label>
                <textarea
                  className="form-textarea"
                  value={example}
                  onChange={e => setExample(e.target.value)}
                  placeholder="இந்தச் சொல்லைப் பயன்படுத்தி ஒரு வாக்கியம்…"
                  rows={2}
                />
              </div>

              <div className="form-group">
                <label className="form-label">வட்டாரம் / வழக்கு — Region / Dialect</label>
                <input
                  className="form-input"
                  type="text"
                  value={region}
                  onChange={e => setRegion(e.target.value)}
                  placeholder="எ.கா.: யாழ்ப்பாணம், மதுரை, மலேசியம்…"
                  style={{ fontFamily: 'var(--font-ui)' }}
                />
              </div>

              <div className="form-group">
                <label className="form-label">ஆதாரம் — Source / Reference</label>
                <input
                  className="form-input"
                  type="text"
                  value={source}
                  onChange={e => setSource(e.target.value)}
                  placeholder="புத்தகம், இணையதளம், ஆய்வு…"
                  style={{ fontFamily: 'var(--font-ui)' }}
                />
              </div>
            </>
          )}

          {error && (
            <div style={{ background: 'rgba(240,106,106,0.1)', border: '1px solid var(--color-accent)', borderRadius: 8, padding: 12, color: 'var(--color-accent)', fontSize: '0.9rem', marginBottom: 12 }}>
              {error}
            </div>
          )}

          <div style={{ display: 'flex', gap: 10 }}>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '⏳ சமர்ப்பிக்கிறது…' : '✅ சமர்ப்பிக்கவும்'}
            </button>
            <button type="button" className="btn btn-outline" onClick={onBack}>ரத்து செய்</button>
          </div>
        </form>
      </div>
    </div>
  )
}
