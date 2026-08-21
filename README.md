# 📚 Tamil Dictionary — திறந்த தமிழ் அகராதி

A professional, open-source Tamil lexical dictionary with community contributions, editorial review, and blog embeddability.

---

## Architecture

```
Tamil Dictionary/
├── backend/          # FastAPI + PostgreSQL API
│   └── app/
│       ├── models.py         # SQLAlchemy ORM (all entities)
│       ├── routers/
│       │   ├── search.py     # Tamil/English/transliteration search
│       │   ├── words.py      # Full word detail API
│       │   ├── community.py  # Contributions, votes, reports
│       │   ├── admin.py      # Editorial review queue
│       │   └── auth.py       # JWT authentication
│       └── schemas.py        # Pydantic response models
│
├── frontend/         # React + Vite embeddable widget
│   └── src/
│       ├── App.tsx                       # Main app + admin routing
│       ├── components/
│       │   ├── SearchBar.tsx             # Live debounced search
│       │   ├── WordEntry.tsx             # Full dictionary entry view
│       │   ├── ContributionForm.tsx      # Community submission form
│       │   └── AdminDashboard.tsx        # Editorial review interface
│       ├── api.ts                        # API client
│       └── index.css                     # Complete design system
│
├── database/
│   ├── schema.sql    # Full PostgreSQL schema (4-layer architecture)
│   └── seed.sql      # 25 seed words with senses, examples, sources
│
├── docs/
│   └── blogger-embed.html   # Blogger integration snippet
│
├── docker-compose.yml        # Full stack local development
└── collect_tamil_words.py    # Multi-source word collector
```

---

## Quick Start

### Option 1 — Docker (Recommended)

```bash
docker-compose up
```

- Dictionary UI: http://localhost:5173
- API docs:      http://localhost:8000/docs
- Admin panel:   http://localhost:5173/#/admin

### Option 2 — Manual

**Backend:**
```bash
cd backend
pip install -r requirements.txt

# Set up PostgreSQL and run schema
psql -U postgres -c "CREATE DATABASE tamildict;"
psql -U postgres -d tamildict -f ../database/schema.sql
psql -U postgres -d tamildict -f ../database/seed.sql

# Configure connection
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/tamildict"

uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/search?q=அன்பு` | Search Tamil, English, transliteration |
| `GET`  | `/api/words/{id}` | Full word detail with senses |
| `GET`  | `/api/words/{id}/community` | Published community contributions |
| `POST` | `/api/contribute` | Submit a community contribution |
| `POST` | `/api/vote` | Vote on a contribution |
| `POST` | `/api/report` | Report a contribution |
| `POST` | `/api/request-word` | Request a missing word |
| `POST` | `/api/auth/login` | Editor/admin authentication |
| `GET`  | `/admin/queue` | Editorial review queue |
| `POST` | `/admin/review/{id}` | Accept / reject contribution |

Full interactive docs at **http://localhost:8000/docs**

---

## Embedding in Blogger

```html
<div id="tamil-dictionary-root"></div>
<script>
  window.TamilDictConfig = {
    apiBase: "https://your-api.com"
  };
</script>
<script src="https://your-cdn/tamil-dict-widget.js" defer></script>
```

See `docs/blogger-embed.html` for the complete snippet.

---

## Data Architecture — 4 Layers

| Layer | Purpose | Status |
|-------|---------|--------|
| **A — Canonical** | Editor-verified definitions, senses, examples | ✅ Built |
| **B — Sources** | Provenance: books, corpora, references | ✅ Built |
| **C — Community** | Unverified contributions, votes, reports | ✅ Built |
| **D — Discussion** | Discussion threads per word/sense | ✅ Built |

### Key Principle

```
Community Contribution
        ↓
  Editorial Review
        ↓
  Canonical Lexicon
```

Community contributions **never** auto-publish into canonical data.

---

## Word Model

One word → multiple senses:

```
பால் (paal)
├── Sense 1: Milk
├── Sense 2: Side / Direction
├── Sense 3: Gender (grammatical)
└── Sense 4: Share / Portion
```

Each sense has its own: definitions (Tamil + English), examples, synonyms, antonyms, sources, literary quotations.

---

## Collect More Words

Run the multi-source word collector (10 open corpora):

```bash
pip install requests
python collect_tamil_words.py
```

Sources: Tamil Wiktionary, AI4Bharat, Open-Tamil, Tamil Wikipedia, GitHub word lists, Kaikki.org, and more.

---

## Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1 — Architecture | ✅ Done | Data model, API design, embed strategy |
| 2 — MVP | ✅ Done | Search, word entry, community, editorial UI |
| 3 — Morphology | 🔲 Next | Inflected form lookup engine |
| 4 — Audio | 🔲 Future | Pronunciation upload & playback |
| 5 — Corpus | 🔲 Future | Full-text evidence search |
| 6 — Scale | 🔲 Future | OpenSearch at millions of entries |
| 7 — Public API | 🔲 Future | Downloadable data releases |

---

## License

- **Software**: MIT License
- **Dictionary Data**: Each entry retains source provenance. See `source_works` table for per-source licensing.

---

*Tamil Dictionary — Building a lasting open lexical resource for the Tamil language.*
