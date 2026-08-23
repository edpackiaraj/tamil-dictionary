"""
Search router — Tamil, English, and transliteration search (no pg_trgm required)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import Optional
from app.database import get_db
from app.models import Word, Sense, Definition, MorphologicalForm, ZeroResultSearch
from app.schemas import SearchResultItem, SearchResponse

router = APIRouter()


def is_tamil(q: str) -> bool:
    return any("\u0B80" <= c <= "\u0BFF" for c in q)


import os
import aiosqlite

async def get_sqlite_db_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # Look in root or in data/
    path1 = os.path.join(base_dir, "tamil_dictionary.db")
    path2 = os.path.join(base_dir, "data", "tamil_dictionary.db")
    return path2 if os.path.exists(path2) else path1

@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=200),
    lang: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    q = q.strip()
    results = []

    if is_tamil(q):
        results = await _search_tamil(db, q, limit, offset)
    else:
        results = await _search_mixed(db, q, limit, offset)

    # Fallback to massive SQLite database
    if len(results) < limit:
        sqlite_results = await _search_sqlite(q, limit - len(results), offset)
        results.extend(sqlite_results)

    if not results:
        await _track_zero_result(db, q)

    return SearchResponse(query=q, total=len(results), results=results)

async def _search_sqlite(q: str, limit: int, offset: int) -> list[SearchResultItem]:
    db_path = await get_sqlite_db_path()
    if not os.path.exists(db_path):
        return []
    
    results = []
    try:
        async with aiosqlite.connect(db_path) as conn:
            # Query the flat table
            if is_tamil(q):
                query = "SELECT id, word, meaning_tamil, meaning_english, part_of_speech FROM words WHERE word LIKE ? LIMIT ? OFFSET ?"
                cursor = await conn.execute(query, (f"%{q}%", limit, offset))
            else:
                query = "SELECT id, word, meaning_tamil, meaning_english, part_of_speech FROM words WHERE meaning_english LIKE ? LIMIT ? OFFSET ?"
                cursor = await conn.execute(query, (f"%{q}%", limit, offset))
            
            rows = await cursor.fetchall()
            for row in rows:
                results.append(SearchResultItem(
                    id=f"SQLITE-{row[0]}",
                    headword=row[1] or "",
                    transliteration=None,
                    pos_tamil=None,
                    pos_english=row[4],
                    first_english_def=row[3],
                    first_tamil_def=row[2],
                    sense_count=1
                ))
    except Exception as e:
        print(f"SQLite search error: {e}")
    return results


async def _search_tamil(db: AsyncSession, q: str, limit: int, offset: int):
    """Search by Tamil headword using ILIKE — no pg_trgm needed."""
    stmt = (
        select(Word)
        .where(
            Word.lexical_status == "published",
            or_(
                Word.headword == q,
                Word.headword.ilike(f"{q}%"),
                Word.headword.ilike(f"%{q}%"),
            )
        )
        .order_by(
            # Exact match first, then prefix, then contains
            (Word.headword == q).desc(),
            Word.headword,
        )
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).scalars().all()

    # Fallback: morphological forms
    if not rows:
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


async def _search_mixed(db: AsyncSession, q: str, limit: int, offset: int):
    """Search by transliteration and English definition using ILIKE — no pg_trgm needed."""
    stmt = (
        select(Word)
        .outerjoin(Sense, Sense.word_id == Word.id)
        .outerjoin(Definition, Definition.sense_id == Sense.id)
        .where(
            Word.lexical_status == "published",
            or_(
                Word.transliteration.ilike(f"{q}%"),
                Word.transliteration.ilike(f"%{q}%"),
                Definition.definition.ilike(f"%{q}%"),
            )
        )
        .distinct()
        .order_by(Word.transliteration)
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [await _to_result_item(db, w) for w in rows]


async def _to_result_item(db: AsyncSession, word: Word) -> SearchResultItem:
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

    sense_count = (await db.execute(
        select(func.count()).where(Sense.word_id == word.id)
    )).scalar_one()

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
