"""
Search router — handles Tamil, English, and transliteration search
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, text
from typing import Optional
from app.database import get_db
from app.models import Word, Sense, Definition, MorphologicalForm, ZeroResultSearch
from app.schemas import SearchResultItem, SearchResponse

router = APIRouter()

TAMIL_RANGE = "\u0B80-\u0BFF"


def is_tamil(q: str) -> bool:
    return any("\u0B80" <= c <= "\u0BFF" for c in q)


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    lang: Optional[str] = Query(None, description="Hint: 'ta', 'en', 'transliteration'"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    q = q.strip()
    results = []

    if is_tamil(q):
        results = await _search_tamil(db, q, limit, offset)
    elif lang == "transliteration" or not is_tamil(q) and len(q) <= 30:
        # try both transliteration and English
        results = await _search_mixed(db, q, limit, offset)
    else:
        results = await _search_english(db, q, limit, offset)

    # Track zero results
    if not results:
        await _track_zero_result(db, q)

    return SearchResponse(query=q, total=len(results), results=results)


async def _search_tamil(db: AsyncSession, q: str, limit: int, offset: int):
    # 1. Exact match
    # 2. Morphological form match
    # 3. Trigram similarity
    stmt = (
        select(Word)
        .where(
            Word.lexical_status == "published",
            or_(
                Word.headword == q,
                Word.headword.ilike(f"{q}%"),
                func.similarity(Word.headword, q) > 0.3,
            )
        )
        .order_by(
            (Word.headword == q).desc(),
            func.similarity(Word.headword, q).desc(),
        )
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).scalars().all()

    # Also search morphological forms
    if len(rows) == 0:
        morph_stmt = (
            select(Word)
            .join(MorphologicalForm, MorphologicalForm.word_id == Word.id)
            .where(
                Word.lexical_status == "published",
                MorphologicalForm.form == q,
            )
            .limit(limit)
        )
        rows = (await db.execute(morph_stmt)).scalars().all()

    return [await _to_result_item(db, w) for w in rows]


async def _search_english(db: AsyncSession, q: str, limit: int, offset: int):
    stmt = (
        select(Word)
        .join(Sense, Sense.word_id == Word.id)
        .join(Definition, Definition.sense_id == Sense.id)
        .where(
            Word.lexical_status == "published",
            Definition.language == "en",
            or_(
                Definition.definition.ilike(f"%{q}%"),
                func.similarity(Definition.definition, q) > 0.2,
            )
        )
        .distinct()
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [await _to_result_item(db, w) for w in rows]


async def _search_mixed(db: AsyncSession, q: str, limit: int, offset: int):
    # Transliteration + English in one query
    stmt = (
        select(Word)
        .outerjoin(Sense, Sense.word_id == Word.id)
        .outerjoin(Definition, Definition.sense_id == Sense.id)
        .where(
            Word.lexical_status == "published",
            or_(
                Word.transliteration.ilike(f"{q}%"),
                func.similarity(Word.transliteration, q) > 0.4,
                Definition.definition.ilike(f"%{q}%"),
            )
        )
        .distinct()
        .order_by(func.similarity(Word.transliteration, q).desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [await _to_result_item(db, w) for w in rows]


async def _to_result_item(db: AsyncSession, word: Word) -> SearchResultItem:
    # Get first English definition
    stmt = (
        select(Definition.definition)
        .join(Sense, Definition.sense_id == Sense.id)
        .where(Sense.word_id == word.id, Definition.language == "en")
        .order_by(Sense.sense_number, Definition.sort_order)
        .limit(1)
    )
    en_def = (await db.execute(stmt)).scalar_one_or_none()

    stmt_ta = (
        select(Definition.definition)
        .join(Sense, Definition.sense_id == Sense.id)
        .where(Sense.word_id == word.id, Definition.language == "ta")
        .order_by(Sense.sense_number, Definition.sort_order)
        .limit(1)
    )
    ta_def = (await db.execute(stmt_ta)).scalar_one_or_none()

    sense_count_stmt = select(func.count()).where(Sense.word_id == word.id)
    sense_count = (await db.execute(sense_count_stmt)).scalar_one()

    return SearchResultItem(
        id=word.id,
        headword=word.headword,
        transliteration=word.transliteration,
        pos_tamil=word.part_of_speech.tamil_label if word.part_of_speech else None,
        pos_english=word.part_of_speech.english_label if word.part_of_speech else None,
        first_english_def=en_def,
        first_tamil_def=ta_def,
        sense_count=sense_count,
    )


async def _track_zero_result(db: AsyncSession, q: str):
    try:
        existing = await db.get(ZeroResultSearch, q)
        if existing:
            existing.count += 1
            existing.last_seen = func.now()
        else:
            db.add(ZeroResultSearch(query=q, count=1))
        await db.commit()
    except Exception:
        await db.rollback()
