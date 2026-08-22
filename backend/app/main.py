"""
FastAPI main application — Tamil Dictionary API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.routers import search, words, community, admin, auth, morphology
from app.database import engine
from sqlalchemy import text

import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _seed(conn):
    """Insert all reference and word data. Every statement is idempotent."""

    # ── Parts of speech ──────────────────────────────────────────────────────
    await conn.execute(text("""
        INSERT INTO parts_of_speech (id, code, tamil_label, english_label, sort_order) VALUES
        (1,'noun',      'பெயர்ச்சொல்', 'Noun',      1),
        (2,'verb',      'வினைச்சொல்',  'Verb',      2),
        (3,'adjective', 'பெயரடை',      'Adjective', 3),
        (4,'adverb',    'வினையடை',     'Adverb',    4),
        (5,'pronoun',   'பிரதிப்பெயர்','Pronoun',   5),
        (6,'particle',  'இடைச்சொல்',   'Particle',  6),
        (7,'idiom',     'மரபுத்தொடர்', 'Idiom',     7),
        (8,'phrase',    'சொற்றொடர்',   'Phrase',    8)
        ON CONFLICT (code) DO NOTHING
    """))

    # ── Usage labels ──────────────────────────────────────────────────────────
    await conn.execute(text("""
        INSERT INTO usage_labels (code, tamil_label, english_label, category) VALUES
        ('literary',   'இலக்கியம்',     'Literary',       'register'),
        ('colloquial', 'பேச்சுவழக்கு',  'Colloquial',     'register'),
        ('formal',     'முறைமையான',     'Formal',         'register'),
        ('archaic',    'பழமையானது',     'Archaic',        'period'),
        ('modern',     'நவீனப் பயன்பாடு','Modern',        'period'),
        ('computing',  'கணினி',         'Computing',      'domain'),
        ('medicine',   'மருத்துவம்',    'Medicine',       'domain'),
        ('law',        'சட்டம்',        'Law',            'domain'),
        ('jaffna',     'யாழ்ப்பாணம்',  'Jaffna dialect', 'dialect'),
        ('madurai',    'மதுரை',         'Madurai dialect','dialect'),
        ('regional',   'வட்டார வழக்கு','Regional',       'dialect'),
        ('obsolete',   'வழக்கொழிந்தது','Obsolete',       'status'),
        ('technical',  'தொழில்நுட்பம்','Technical',      'domain')
        ON CONFLICT (code) DO NOTHING
    """))

    # ── Source works ──────────────────────────────────────────────────────────
    await conn.execute(text("""
        INSERT INTO source_works (id, title, title_tamil, author, year, url, license, copyright_status, may_reproduce) VALUES
        (1,'Tamil Lexicon',         'தமிழ் அகராதி',  'University of Madras', 1924,'https://www.tamildigitallibrary.in','public_domain','public_domain',TRUE),
        (2,'Thirukkural',           'திருக்குறள்',   'Thiruvalluvar',         0,   'https://www.projectmadurai.org',    'public_domain','public_domain',TRUE),
        (3,'Project Madurai Corpus','திட்ட மதுரை',   'Various',              2000, 'https://www.projectmadurai.org',    'CC-BY',        'open',         TRUE)
        ON CONFLICT (id) DO NOTHING
    """))

    # ── 25 words ──────────────────────────────────────────────────────────────
    await conn.execute(text("""
        INSERT INTO words (id, headword, headword_normalized, transliteration, part_of_speech_id, lexical_status, is_compound, is_proper_noun, created_at, updated_at, revision) VALUES
        ('TA-000001','அன்பு',    'அன்பு',    'anbu',     1,'published',false,false,now(),now(),1),
        ('TA-000002','அகம்',     'அகம்',     'agam',     1,'published',false,false,now(),now(),1),
        ('TA-000003','அறம்',     'அறம்',     'aram',     1,'published',false,false,now(),now(),1),
        ('TA-000004','இன்பம்',   'இன்பம்',   'inbam',    1,'published',false,false,now(),now(),1),
        ('TA-000005','உண்மை',    'உண்மை',    'unmai',    1,'published',false,false,now(),now(),1),
        ('TA-000006','கடல்',     'கடல்',     'kadal',    1,'published',false,false,now(),now(),1),
        ('TA-000007','பால்',     'பால்',     'paal',     1,'published',false,false,now(),now(),1),
        ('TA-000008','வீடு',     'வீடு',     'veedu',    1,'published',false,false,now(),now(),1),
        ('TA-000009','மரம்',     'மரம்',     'maram',    1,'published',false,false,now(),now(),1),
        ('TA-000010','நீர்',     'நீர்',     'neer',     1,'published',false,false,now(),now(),1),
        ('TA-000011','செய்',     'செய்',     'sei',      2,'published',false,false,now(),now(),1),
        ('TA-000012','படி',      'படி',      'padi',     2,'published',false,false,now(),now(),1),
        ('TA-000013','நடை',      'நடை',      'nadai',    1,'published',false,false,now(),now(),1),
        ('TA-000014','கண்',      'கண்',      'kan',      1,'published',false,false,now(),now(),1),
        ('TA-000015','நாடு',     'நாடு',     'naadu',    1,'published',false,false,now(),now(),1),
        ('TA-000016','மக்கள்',   'மக்கள்',   'makkal',   1,'published',false,false,now(),now(),1),
        ('TA-000017','இரவு',     'இரவு',     'iravu',    1,'published',false,false,now(),now(),1),
        ('TA-000018','பகல்',     'பகல்',     'pagal',    1,'published',false,false,now(),now(),1),
        ('TA-000019','வெளி',     'வெளி',     'veli',     1,'published',false,false,now(),now(),1),
        ('TA-000020','தமிழ்',    'தமிழ்',    'thamizh',  1,'published',false,false,now(),now(),1),
        ('TA-000021','சொல்',     'சொல்',     'sol',      1,'published',false,false,now(),now(),1),
        ('TA-000022','மொழி',     'மொழி',     'mozhi',    1,'published',false,false,now(),now(),1),
        ('TA-000023','அரசு',     'அரசு',     'arasu',    1,'published',false,false,now(),now(),1),
        ('TA-000024','குழந்தை',  'குழந்தை',  'kuzhandai',1,'published',false,false,now(),now(),1),
        ('TA-000025','தாய்',     'தாய்',     'thaay',    1,'published',false,false,now(),now(),1)
        ON CONFLICT (id) DO NOTHING
    """))

    # ── Senses ────────────────────────────────────────────────────────────────
    # அன்பு — 2 senses
    await conn.execute(text("""
        INSERT INTO senses (word_id, sense_number, status) VALUES
        ('TA-000001',1,'published'),('TA-000001',2,'published'),
        ('TA-000003',1,'published'),('TA-000003',2,'published'),
        ('TA-000006',1,'published'),
        ('TA-000007',1,'published'),('TA-000007',2,'published'),
        ('TA-000007',3,'published'),('TA-000007',4,'published'),
        ('TA-000008',1,'published'),('TA-000008',2,'published'),
        ('TA-000020',1,'published'),
        ('TA-000002',1,'published'),('TA-000004',1,'published'),
        ('TA-000005',1,'published'),('TA-000009',1,'published'),
        ('TA-000010',1,'published'),('TA-000011',1,'published'),
        ('TA-000012',1,'published'),('TA-000013',1,'published'),
        ('TA-000014',1,'published'),('TA-000015',1,'published'),
        ('TA-000016',1,'published'),('TA-000017',1,'published'),
        ('TA-000018',1,'published'),('TA-000019',1,'published'),
        ('TA-000021',1,'published'),('TA-000022',1,'published'),
        ('TA-000023',1,'published'),('TA-000024',1,'published'),
        ('TA-000025',1,'published')
        ON CONFLICT (word_id, sense_number) DO NOTHING
    """))

    # ── Definitions ───────────────────────────────────────────────────────────
    await conn.execute(text("""
        INSERT INTO definitions (sense_id, language, definition, sort_order)
        SELECT s.id, d.lang, d.def, 0
        FROM senses s
        JOIN words w ON w.id = s.word_id
        JOIN (VALUES
            ('TA-000001',1,'en','Love; affection; tender feeling towards another'),
            ('TA-000001',1,'ta','பாசம்; ஒருவர் மீது கொள்ளும் அன்னிய உணர்வு'),
            ('TA-000001',2,'en','Kindness; benevolence'),
            ('TA-000001',2,'ta','இரக்கம்; கருணை'),
            ('TA-000002',1,'en','Interior; inner world; home'),
            ('TA-000002',1,'ta','உள்ளிடம்; இல்லம்; உள்ளம்'),
            ('TA-000003',1,'en','Virtue; righteousness; moral duty'),
            ('TA-000003',1,'ta','நீதி; ஒழுக்கம்; தர்மம்'),
            ('TA-000003',2,'en','Charity; alms-giving'),
            ('TA-000003',2,'ta','தானம்; கொடை'),
            ('TA-000004',1,'en','Happiness; pleasure; joy'),
            ('TA-000004',1,'ta','மகிழ்ச்சி; நந்தம்; ஆனந்தம்'),
            ('TA-000005',1,'en','Truth; reality; genuineness'),
            ('TA-000005',1,'ta','உண்மை; யதார்த்தம்'),
            ('TA-000006',1,'en','Sea; ocean; a large body of salt water'),
            ('TA-000006',1,'ta','கடல்; மகாசமுத்திரம்; உப்பு நீர் நிறைந்த பரந்த நீர்நிலை'),
            ('TA-000007',1,'en','Milk; the white liquid produced by mammals'),
            ('TA-000007',1,'ta','பசும்பால்; பாலூட்டும் விலங்குகள் உற்பத்தி செய்யும் வெண்மையான திரவம்'),
            ('TA-000007',2,'en','Side; direction; part'),
            ('TA-000007',2,'ta','பக்கம்; திசை'),
            ('TA-000007',3,'en','Gender (grammatical or biological)'),
            ('TA-000007',3,'ta','ஆண்பால், பெண்பால் போன்ற இலக்கண வகை'),
            ('TA-000007',4,'en','Share; portion; lot'),
            ('TA-000007',4,'ta','பங்கு; ஒரு பகுதி'),
            ('TA-000008',1,'en','House; home; dwelling place'),
            ('TA-000008',1,'ta','இல்லம்; குடியிருக்கும் இடம்'),
            ('TA-000008',2,'en','Liberation; moksha (spiritual sense)'),
            ('TA-000008',2,'ta','முக்தி; வீடுபேறு; மோட்சம்'),
            ('TA-000009',1,'en','Tree; plant with a woody trunk'),
            ('TA-000009',1,'ta','தாவரம்; கட்டைத் தண்டு கொண்ட தாவர வகை'),
            ('TA-000010',1,'en','Water; river water (distinguished from salt water)'),
            ('TA-000010',1,'ta','நீர்; தண்ணீர்; ஆற்று நீர்'),
            ('TA-000011',1,'en','To do; to make; to perform'),
            ('TA-000011',1,'ta','செய்தல்; உருவாக்குதல்'),
            ('TA-000012',1,'en','To read; to study; to climb'),
            ('TA-000012',1,'ta','படித்தல்; ஏறுதல்; ஓதுதல்'),
            ('TA-000013',1,'en','Walking; gait; manner; way'),
            ('TA-000013',1,'ta','நடைபோடல்; செல்லும் விதம்'),
            ('TA-000014',1,'en','Eye; sight'),
            ('TA-000014',1,'ta','கண்; பார்வை உறுப்பு'),
            ('TA-000015',1,'en','Country; nation; land'),
            ('TA-000015',1,'ta','நாடு; தேசம்; பூமி'),
            ('TA-000016',1,'en','People; citizens; populace'),
            ('TA-000016',1,'ta','மனிதர்கள்; குடிமக்கள்'),
            ('TA-000017',1,'en','Night; nighttime'),
            ('TA-000017',1,'ta','இரவு; இரவுப்பொழுது'),
            ('TA-000018',1,'en','Daytime; daylight'),
            ('TA-000018',1,'ta','பகல்; பகல்பொழுது; வெளிச்சம்'),
            ('TA-000019',1,'en','Outside; open space; sky'),
            ('TA-000019',1,'ta','வெளியிடம்; திறந்தவெளி; ஆகாயம்'),
            ('TA-000020',1,'en','Tamil language; one of the oldest classical languages of the world'),
            ('TA-000020',1,'ta','தமிழ் மொழி; உலகின் மிகப் பழமையான செம்மொழிகளில் ஒன்று'),
            ('TA-000021',1,'en','Word; term'),
            ('TA-000021',1,'ta','வார்த்தை; சொற்கோவை'),
            ('TA-000022',1,'en','Language; tongue'),
            ('TA-000022',1,'ta','மொழி; நாவால் வெளிப்படுத்தும் கருவி'),
            ('TA-000023',1,'en','Government; rule; king'),
            ('TA-000023',1,'ta','அரசாட்சி; ஆட்சி; மன்னன்'),
            ('TA-000024',1,'en','Child; infant'),
            ('TA-000024',1,'ta','குழந்தை; சிறுவன்/சிறுமி'),
            ('TA-000025',1,'en','Mother'),
            ('TA-000025',1,'ta','அன்னை; ஜனனி; தாய்')
        ) AS d(word_id, sense_num, lang, def)
          ON w.id = d.word_id AND s.sense_number = d.sense_num
        ON CONFLICT DO NOTHING
    """))

    # ── Synonyms ──────────────────────────────────────────────────────────────
    await conn.execute(text("""
        INSERT INTO synonyms (sense_id, synonym, sort_order)
        SELECT s.id, syn.word, syn.ord
        FROM senses s JOIN words w ON w.id = s.word_id
        JOIN (VALUES
            ('TA-000001',1,'பாசம்',1),('TA-000001',1,'நேசம்',2),('TA-000001',1,'காதல்',3),
            ('TA-000001',2,'கருணை',1),('TA-000001',2,'இரக்கம்',2),
            ('TA-000006',1,'சமுத்திரம்',1),('TA-000006',1,'ஆழி',2),('TA-000006',1,'பரவை',3)
        ) AS syn(word_id, sense_num, word, ord)
          ON w.id = syn.word_id AND s.sense_number = syn.sense_num
        ON CONFLICT DO NOTHING
    """))

    # ── Examples ──────────────────────────────────────────────────────────────
    await conn.execute(text("""
        INSERT INTO examples (sense_id, example_tamil, example_english, sort_order)
        SELECT s.id, ex.ta, ex.en, ex.ord
        FROM senses s JOIN words w ON w.id = s.word_id
        JOIN (VALUES
            ('TA-000001',1,'அன்பே சிவம்','Love is God',1),
            ('TA-000001',1,'தாய் அன்பு ஒப்பற்றது','A mother''s love is incomparable',2)
        ) AS ex(word_id, sense_num, ta, en, ord)
          ON w.id = ex.word_id AND s.sense_number = ex.sense_num
        ON CONFLICT DO NOTHING
    """))

    # ── Morphological forms (வீடு) ────────────────────────────────────────────
    await conn.execute(text("""
        INSERT INTO morphological_forms (word_id, form, form_type, generated) VALUES
        ('TA-000008','வீட்டில்',    'locative',        TRUE),
        ('TA-000008','வீட்டுக்கு',  'dative',          TRUE),
        ('TA-000008','வீட்டை',      'accusative',      TRUE),
        ('TA-000008','வீடுகள்',     'plural',          TRUE),
        ('TA-000008','வீடுகளில்',   'plural_locative', TRUE)
        ON CONFLICT (word_id, form_type) DO NOTHING
    """))

    # ── Quotations ────────────────────────────────────────────────────────────
    await conn.execute(text("""
        INSERT INTO quotations (sense_id, quotation_tamil, source_work_id, verse, century)
        SELECT s.id, q.text, q.src, q.verse, q.century
        FROM senses s JOIN words w ON w.id = s.word_id
        JOIN (VALUES
            ('TA-000006',1,'யாதும் ஊரே யாவரும் கேளிர்',2,'192','2nd BCE'),
            ('TA-000003',1,'அறத்தாறு இதுவென வேண்டா சிவிகை',2,'4','2nd BCE')
        ) AS q(word_id, sense_num, text, src, verse, century)
          ON w.id = q.word_id AND s.sense_number = q.sense_num
        ON CONFLICT DO NOTHING
    """))

    # ── Source associations ───────────────────────────────────────────────────
    await conn.execute(text("""
        INSERT INTO sense_sources (sense_id, source_work_id, page_ref)
        SELECT s.id, ss.src, ss.pg
        FROM senses s JOIN words w ON w.id = s.word_id
        JOIN (VALUES
            ('TA-000001',1,1,'vol.1 p.12'),
            ('TA-000003',1,1,'vol.3 p.88'),
            ('TA-000006',1,1,'vol.2 p.44'),
            ('TA-000003',1,2,'Kural 1')
        ) AS ss(word_id, sense_num, src, pg)
          ON w.id = ss.word_id AND s.sense_number = ss.sense_num
        ON CONFLICT DO NOTHING
    """))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Auto-initialize DB schema and seed full data on first startup."""
    logger.info("Startup: checking database...")
    try:
        from app import models  # noqa: F401
        from app.database import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Tables created / verified via SQLAlchemy.")
            count = (await conn.execute(text("SELECT COUNT(*) FROM parts_of_speech"))).scalar()

        if count == 0:
            logger.info("Seeding full dictionary data (25 words)...")
            async with engine.begin() as conn:
                await _seed(conn)
            logger.info("Seed complete.")
        else:
            logger.info(f"DB already seeded ({count} POS rows) — skipping.")

    except Exception as e:
        logger.error(f"DB Init Error: {e}\n{traceback.format_exc()}")

    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Professional Tamil Lexical Dictionary API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router,     prefix="/api",      tags=["Search"])
app.include_router(words.router,      prefix="/api",      tags=["Words"])
app.include_router(community.router,  prefix="/api",      tags=["Community"])
app.include_router(admin.router,      prefix="/admin",    tags=["Admin"])
app.include_router(auth.router,       prefix="/api/auth", tags=["Auth"])
app.include_router(morphology.router, prefix="/api",      tags=["Morphology"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "app": settings.app_name, "version": settings.version}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
