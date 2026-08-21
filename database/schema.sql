-- ============================================================
-- TAMIL DICTIONARY — CANONICAL LEXICAL DATABASE SCHEMA
-- PostgreSQL 16+
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- LAYER A — CANONICAL LEXICAL DATA
-- ============================================================

CREATE TABLE parts_of_speech (
    id            SERIAL PRIMARY KEY,
    code          TEXT UNIQUE NOT NULL,
    tamil_label   TEXT NOT NULL,
    english_label TEXT NOT NULL,
    sort_order    INT DEFAULT 0
);

CREATE TABLE usage_labels (
    id            SERIAL PRIMARY KEY,
    code          TEXT UNIQUE NOT NULL,
    tamil_label   TEXT NOT NULL,
    english_label TEXT NOT NULL,
    category      TEXT NOT NULL
);

CREATE TABLE words (
    id                  TEXT PRIMARY KEY,
    headword            TEXT NOT NULL,
    headword_normalized TEXT NOT NULL,
    alternate_spellings TEXT[],
    transliteration     TEXT,
    transliteration_iso TEXT,
    pronunciation_ipa   TEXT,
    pronunciation_audio TEXT,
    part_of_speech_id   INT REFERENCES parts_of_speech(id),
    lexical_status      TEXT DEFAULT 'published'
                        CHECK (lexical_status IN ('draft','under_review','verified','published','deprecated','disputed')),
    is_compound         BOOLEAN DEFAULT FALSE,
    is_proper_noun      BOOLEAN DEFAULT FALSE,
    frequency_rank      INT,
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now(),
    created_by          UUID,
    revision            INT DEFAULT 1
);

CREATE INDEX idx_words_headword ON words USING gin(headword gin_trgm_ops);
CREATE INDEX idx_words_normalized ON words(headword_normalized);
CREATE INDEX idx_words_transliteration ON words USING gin(transliteration gin_trgm_ops);

CREATE TABLE senses (
    id                SERIAL PRIMARY KEY,
    word_id           TEXT NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    sense_number      INT NOT NULL,
    part_of_speech_id INT REFERENCES parts_of_speech(id),
    domain            TEXT,
    status            TEXT DEFAULT 'published'
                      CHECK (status IN ('draft','under_review','verified','published','deprecated','disputed')),
    created_at        TIMESTAMPTZ DEFAULT now(),
    updated_at        TIMESTAMPTZ DEFAULT now(),
    UNIQUE(word_id, sense_number)
);

CREATE TABLE definitions (
    id         SERIAL PRIMARY KEY,
    sense_id   INT NOT NULL REFERENCES senses(id) ON DELETE CASCADE,
    language   TEXT NOT NULL CHECK (language IN ('ta', 'en')),
    definition TEXT NOT NULL,
    sort_order INT DEFAULT 0
);

CREATE INDEX idx_def_en ON definitions USING gin(definition gin_trgm_ops) WHERE language = 'en';

CREATE TABLE sense_usage_labels (
    sense_id       INT REFERENCES senses(id) ON DELETE CASCADE,
    usage_label_id INT REFERENCES usage_labels(id) ON DELETE CASCADE,
    PRIMARY KEY (sense_id, usage_label_id)
);

CREATE TABLE examples (
    id              SERIAL PRIMARY KEY,
    sense_id        INT NOT NULL REFERENCES senses(id) ON DELETE CASCADE,
    example_tamil   TEXT NOT NULL,
    example_english TEXT,
    source_work_id  INT,
    verified        BOOLEAN DEFAULT FALSE,
    sort_order      INT DEFAULT 0
);

CREATE TABLE synonyms (
    id          SERIAL PRIMARY KEY,
    sense_id    INT NOT NULL REFERENCES senses(id) ON DELETE CASCADE,
    synonym     TEXT NOT NULL,
    word_id_ref TEXT REFERENCES words(id),
    sort_order  INT DEFAULT 0
);

CREATE TABLE antonyms (
    id          SERIAL PRIMARY KEY,
    sense_id    INT NOT NULL REFERENCES senses(id) ON DELETE CASCADE,
    antonym     TEXT NOT NULL,
    word_id_ref TEXT REFERENCES words(id),
    sort_order  INT DEFAULT 0
);

CREATE TABLE related_words (
    id              SERIAL PRIMARY KEY,
    word_id         TEXT NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    related_word_id TEXT NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    relation_type   TEXT NOT NULL,
    UNIQUE(word_id, related_word_id, relation_type)
);

CREATE TABLE morphological_forms (
    id        SERIAL PRIMARY KEY,
    word_id   TEXT NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    form      TEXT NOT NULL,
    form_type TEXT NOT NULL,
    generated BOOLEAN DEFAULT TRUE,
    UNIQUE(word_id, form_type)
);

CREATE INDEX idx_morph_form ON morphological_forms USING gin(form gin_trgm_ops);

CREATE TABLE etymologies (
    id        SERIAL PRIMARY KEY,
    word_id   TEXT NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    etymology TEXT NOT NULL,
    language  TEXT DEFAULT 'en',
    period    TEXT,
    notes     TEXT
);

-- ============================================================
-- LAYER B — SOURCES
-- ============================================================

CREATE TABLE source_works (
    id               SERIAL PRIMARY KEY,
    title            TEXT NOT NULL,
    title_tamil      TEXT,
    author           TEXT,
    year             INT,
    publisher        TEXT,
    url              TEXT,
    license          TEXT,
    copyright_status TEXT,
    attribution      TEXT,
    may_reproduce    BOOLEAN DEFAULT FALSE,
    notes            TEXT
);

ALTER TABLE examples ADD CONSTRAINT fk_example_source
    FOREIGN KEY (source_work_id) REFERENCES source_works(id);

CREATE TABLE sense_sources (
    id             SERIAL PRIMARY KEY,
    sense_id       INT NOT NULL REFERENCES senses(id) ON DELETE CASCADE,
    source_work_id INT NOT NULL REFERENCES source_works(id),
    page_ref       TEXT,
    quote          TEXT,
    UNIQUE(sense_id, source_work_id)
);

CREATE TABLE quotations (
    id                        SERIAL PRIMARY KEY,
    sense_id                  INT NOT NULL REFERENCES senses(id) ON DELETE CASCADE,
    quotation_tamil           TEXT NOT NULL,
    quotation_transliteration TEXT,
    source_work_id            INT REFERENCES source_works(id),
    chapter                   TEXT,
    verse                     TEXT,
    century                   TEXT,
    verified                  BOOLEAN DEFAULT FALSE
);

-- ============================================================
-- LAYER C — COMMUNITY
-- ============================================================

CREATE TABLE users (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    display_name   TEXT NOT NULL,
    email          TEXT UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    password_hash  TEXT NOT NULL,
    role           TEXT DEFAULT 'contributor'
                   CHECK (role IN ('contributor','editor','admin')),
    is_active      BOOLEAN DEFAULT TRUE,
    joined_at      TIMESTAMPTZ DEFAULT now(),
    last_seen      TIMESTAMPTZ
);

CREATE TABLE contributions (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    word_id        TEXT REFERENCES words(id),
    sense_id       INT REFERENCES senses(id),
    contributor_id UUID REFERENCES users(id),
    type           TEXT NOT NULL CHECK (type IN (
                       'additional_meaning','regional_meaning','modern_usage',
                       'correction','new_word','example','pronunciation',
                       'translation','source','spelling','other'
                   )),
    content        TEXT NOT NULL,
    explanation    TEXT,
    example        TEXT,
    region         TEXT,
    time_period    TEXT,
    source_ref     TEXT,
    status         TEXT DEFAULT 'submitted' CHECK (status IN (
                       'submitted','published','flagged','hidden',
                       'accepted_into_canonical','rejected'
                   )),
    editor_note    TEXT,
    reviewed_by    UUID REFERENCES users(id),
    reviewed_at    TIMESTAMPTZ,
    submitted_at   TIMESTAMPTZ DEFAULT now(),
    helpful_count  INT DEFAULT 0
);

CREATE INDEX idx_contrib_word ON contributions(word_id);
CREATE INDEX idx_contrib_status ON contributions(status);

CREATE TABLE contribution_votes (
    id              SERIAL PRIMARY KEY,
    contribution_id UUID NOT NULL REFERENCES contributions(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id),
    vote            TEXT NOT NULL CHECK (vote IN ('helpful','unhelpful','needs_evidence')),
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(contribution_id, user_id)
);

CREATE TABLE reports (
    id              SERIAL PRIMARY KEY,
    contribution_id UUID REFERENCES contributions(id),
    reporter_id     UUID REFERENCES users(id),
    reason          TEXT NOT NULL,
    status          TEXT DEFAULT 'open' CHECK (status IN ('open','resolved','dismissed')),
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- LAYER D — DISCUSSION
-- ============================================================

CREATE TABLE discussions (
    id              SERIAL PRIMARY KEY,
    word_id         TEXT REFERENCES words(id),
    contribution_id UUID REFERENCES contributions(id),
    body            TEXT NOT NULL,
    author_id       UUID REFERENCES users(id),
    is_closed       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE discussion_replies (
    id            SERIAL PRIMARY KEY,
    discussion_id INT NOT NULL REFERENCES discussions(id) ON DELETE CASCADE,
    body          TEXT NOT NULL,
    author_id     UUID REFERENCES users(id),
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- REVISION HISTORY
-- ============================================================

CREATE TABLE revisions (
    id             SERIAL PRIMARY KEY,
    entity_type    TEXT NOT NULL,
    entity_id      TEXT NOT NULL,
    previous_value JSONB,
    new_value      JSONB,
    editor_id      UUID REFERENCES users(id),
    reason         TEXT,
    created_at     TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_revisions ON revisions(entity_type, entity_id);

-- ============================================================
-- ANALYTICS
-- ============================================================

CREATE TABLE zero_result_searches (
    query     TEXT PRIMARY KEY,
    count     INT DEFAULT 1,
    last_seen TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE word_requests (
    id                SERIAL PRIMARY KEY,
    word              TEXT NOT NULL UNIQUE,
    suggested_meaning TEXT,
    request_count     INT DEFAULT 1,
    status            TEXT DEFAULT 'open'
                      CHECK (status IN ('open','in_progress','added','rejected')),
    created_at        TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- AUTO-UPDATE TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_words_updated BEFORE UPDATE ON words
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_senses_updated BEFORE UPDATE ON senses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- SUMMARY VIEW
-- ============================================================

CREATE VIEW word_summary AS
SELECT
    w.id, w.headword, w.transliteration, w.lexical_status,
    p.tamil_label AS pos_tamil, p.english_label AS pos_english,
    COUNT(DISTINCT s.id) AS sense_count,
    (SELECT d.definition FROM definitions d
     JOIN senses s2 ON d.sense_id = s2.id
     WHERE s2.word_id = w.id AND d.language = 'en'
     ORDER BY s2.sense_number, d.sort_order LIMIT 1) AS first_english_def,
    (SELECT d.definition FROM definitions d
     JOIN senses s2 ON d.sense_id = s2.id
     WHERE s2.word_id = w.id AND d.language = 'ta'
     ORDER BY s2.sense_number, d.sort_order LIMIT 1) AS first_tamil_def
FROM words w
LEFT JOIN parts_of_speech p ON w.part_of_speech_id = p.id
LEFT JOIN senses s ON s.word_id = w.id
WHERE w.lexical_status = 'published'
GROUP BY w.id, p.tamil_label, p.english_label;
