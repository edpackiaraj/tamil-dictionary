"""
Words router — full word detail, senses, community info
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import (Word, Sense, Definition, Example, Synonym, Antonym,
                        Quotation, SenseSource, MorphologicalForm, Etymology,
                        RelatedWord, Contribution)
from app.schemas import WordDetail, SenseDetail

router = APIRouter()


@router.get("/words/{word_id}", response_model=WordDetail)
async def get_word(word_id: str, db: AsyncSession = Depends(get_db)):
    if word_id.startswith("SQLITE-"):
        return await _get_word_sqlite(word_id)
        
    if word_id.startswith("TA-"):
        word = await db.get(Word, word_id)
    else:
        stmt = select(Word).where(Word.headword == word_id, Word.lexical_status == "published")
        word = (await db.execute(stmt)).scalar_one_or_none()

    if not word:
        raise HTTPException(status_code=404, detail="Word not found")

    senses = await _get_senses(db, word.id)
    morph_forms = (await db.execute(
        select(MorphologicalForm).where(MorphologicalForm.word_id == word.id)
    )).scalars().all()
    etymologies = (await db.execute(
        select(Etymology).where(Etymology.word_id == word.id)
    )).scalars().all()

    community_count = (await db.execute(
        select(func.count()).where(
            Contribution.word_id == word.id,
            Contribution.status == "published"
        )
    )).scalar_one()

    return WordDetail(
        id=word.id,
        headword=word.headword,
        transliteration=word.transliteration,
        transliteration_iso=word.transliteration_iso,
        pronunciation_ipa=word.pronunciation_ipa,
        pronunciation_audio=word.pronunciation_audio,
        alternate_spellings=word.alternate_spellings or [],
        pos_tamil=word.part_of_speech.tamil_label if word.part_of_speech else None,
        pos_english=word.part_of_speech.english_label if word.part_of_speech else None,
        lexical_status=word.lexical_status,
        is_compound=word.is_compound,
        senses=senses,
        morphological_forms=[
            {"form": f.form, "form_type": f.form_type, "generated": f.generated}
            for f in morph_forms
        ],
        etymologies=[
            {"etymology": e.etymology, "language": e.language, "period": e.period}
            for e in etymologies
        ],
        community_count=community_count,
        revision=word.revision,
        updated_at=word.updated_at.isoformat() if word.updated_at else None,
    )


async def _get_senses(db: AsyncSession, word_id: str) -> list[SenseDetail]:
    senses_q = (await db.execute(
        select(Sense).where(Sense.word_id == word_id, Sense.status == "published")
        .order_by(Sense.sense_number)
    )).unique().scalars().all()

    result = []
    for sense in senses_q:
        defs = (await db.execute(
            select(Definition).where(Definition.sense_id == sense.id)
            .order_by(Definition.sort_order)
        )).scalars().all()
        examples = (await db.execute(
            select(Example).where(Example.sense_id == sense.id)
            .order_by(Example.sort_order)
        )).scalars().all()
        synonyms = (await db.execute(
            select(Synonym).where(Synonym.sense_id == sense.id)
            .order_by(Synonym.sort_order)
        )).scalars().all()
        antonyms = (await db.execute(
            select(Antonym).where(Antonym.sense_id == sense.id)
            .order_by(Antonym.sort_order)
        )).scalars().all()
        sources = (await db.execute(
            select(SenseSource).where(SenseSource.sense_id == sense.id)
        )).unique().scalars().all()
        quotations = (await db.execute(
            select(Quotation).where(Quotation.sense_id == sense.id)
        )).unique().scalars().all()

        result.append(SenseDetail(
            id=sense.id,
            sense_number=sense.sense_number,
            domain=sense.domain,
            status=sense.status,
            definitions_en=[d.definition for d in defs if d.language == "en"],
            definitions_ta=[d.definition for d in defs if d.language == "ta"],
            examples=[
                {"tamil": e.example_tamil, "english": e.example_english, "verified": e.verified}
                for e in examples
            ],
            synonyms=[s.synonym for s in synonyms],
            antonyms=[a.antonym for a in antonyms],
            sources=[
                {
                    "title": ss.source_work.title if ss.source_work else None,
                    "page_ref": ss.page_ref,
                    "quote": ss.quote,
                }
                for ss in sources
            ],
            quotations=[
                {
                    "text": q.quotation_tamil,
                    "source": q.source_work.title if q.source_work else None,
                    "chapter": q.chapter,
                    "verse": q.verse,
                    "century": q.century,
                    "verified": q.verified,
                }
                for q in quotations
            ],
        ))
    return result


@router.get("/words/{word_id}/community")
async def get_word_community(word_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Contribution)
        .where(Contribution.word_id == word_id, Contribution.status == "published")
        .order_by(Contribution.helpful_count.desc(), Contribution.submitted_at.desc())
    )
    contributions = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": str(c.id),
            "type": c.type,
            "content": c.content,
            "explanation": c.explanation,
            "example": c.example,
            "region": c.region,
            "time_period": c.time_period,
            "contributor": c.contributor.display_name if c.contributor else "Anonymous",
            "submitted_at": c.submitted_at.isoformat(),
            "helpful_count": c.helpful_count,
        }
        for c in contributions
    ]

import os
import aiosqlite
from app.routers.search import get_sqlite_db_path

async def _get_word_sqlite(word_id: str) -> WordDetail:
    db_path = await get_sqlite_db_path()
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="SQLite database not found")
        
    try:
        real_id = int(word_id.split("-")[1])
    except:
        raise HTTPException(status_code=400, detail="Invalid SQLITE ID")
        
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute("SELECT id, word, meaning_tamil, meaning_english, part_of_speech FROM words WHERE id = ?", (real_id,))
        row = await cursor.fetchone()
        
    if not row:
        raise HTTPException(status_code=404, detail="Word not found in SQLite")
        
    sense = SenseDetail(
        id=f"SENSE-SQLITE-{row[0]}",
        sense_number=1,
        domain=None,
        status="published",
        definitions_en=[row[3]] if row[3] else [],
        definitions_ta=[row[2]] if row[2] else [],
        examples=[],
        synonyms=[],
        antonyms=[],
        sources=[],
        quotations=[]
    )
    
    return WordDetail(
        id=word_id,
        headword=row[1] or "",
        transliteration=None,
        transliteration_iso=None,
        pronunciation_ipa=None,
        pronunciation_audio=None,
        alternate_spellings=[],
        pos_tamil=None,
        pos_english=row[4],
        lexical_status="published",
        is_compound=False,
        senses=[sense],
        morphological_forms=[],
        etymologies=[],
        community_count=0,
        revision=1,
        updated_at=None
    )
