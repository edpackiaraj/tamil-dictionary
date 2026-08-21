"""
Morphology router — inflection generation and reverse lookup
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models import Word, MorphologicalForm
from app.morphology import inflect, generate_all_forms, classify

router = APIRouter()


@router.get("/morphology/{word_id}")
async def get_morphology(word_id: str, db: AsyncSession = Depends(get_db)):
    """
    Return all inflected forms for a word.
    If stored forms exist in the DB, return those.
    Otherwise, generate them on the fly from the morphology engine.
    """
    # Accept word ID or headword
    if word_id.startswith("TA-"):
        word = await db.get(Word, word_id)
    else:
        stmt = select(Word).where(Word.headword == word_id)
        word = (await db.execute(stmt)).scalar_one_or_none()

    if not word:
        raise HTTPException(404, "Word not found")

    # Check stored forms
    stored = (await db.execute(
        select(MorphologicalForm).where(MorphologicalForm.word_id == word.id)
    )).scalars().all()

    if stored:
        return {
            "word_id": word.id,
            "headword": word.headword,
            "class": classify(word.headword),
            "source": "database",
            "forms": [
                {"form": f.form, "form_type": f.form_type, "generated": f.generated}
                for f in stored
            ]
        }

    # Generate on the fly
    generated = generate_all_forms(word.headword)

    # Auto-save to DB for future use
    for g in generated:
        try:
            db.add(MorphologicalForm(
                word_id=word.id,
                form=g["form"],
                form_type=g["form_type"],
                generated=True,
            ))
        except Exception:
            pass
    try:
        await db.commit()
    except Exception:
        await db.rollback()

    return {
        "word_id": word.id,
        "headword": word.headword,
        "class": classify(word.headword),
        "source": "generated",
        "forms": generated
    }


@router.get("/morphology/analyze/{form}")
async def analyze_form(
    form: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Reverse morphology lookup — given an inflected form, find the base word.
    e.g., வீட்டில் → வீடு
    """
    # Search in stored morphological forms
    stmt = (
        select(MorphologicalForm)
        .where(MorphologicalForm.form == form)
    )
    matches = (await db.execute(stmt)).scalars().all()

    if matches:
        results = []
        for m in matches:
            word = await db.get(Word, m.word_id)
            if word:
                results.append({
                    "base_word": word.headword,
                    "word_id": word.id,
                    "form_type": m.form_type,
                    "generated": m.generated,
                })
        return {"form": form, "results": results}

    return {"form": form, "results": [], "note": "Not found in stored forms"}


class GenerateBatchRequest(BaseModel):
    word_ids: list[str]


@router.post("/morphology/generate-batch")
async def generate_batch(body: GenerateBatchRequest, db: AsyncSession = Depends(get_db)):
    """
    Batch-generate and store morphological forms for multiple words.
    Useful for bulk processing after importing new words.
    """
    results = {}
    for wid in body.word_ids[:100]:  # cap at 100
        word = await db.get(Word, wid)
        if not word:
            results[wid] = {"error": "not found"}
            continue

        forms = generate_all_forms(word.headword)
        saved = 0
        for g in forms:
            try:
                db.add(MorphologicalForm(
                    word_id=word.id,
                    form=g["form"],
                    form_type=g["form_type"],
                    generated=True,
                ))
                saved += 1
            except Exception:
                pass
        try:
            await db.commit()
        except Exception:
            await db.rollback()
        results[wid] = {"headword": word.headword, "forms_generated": saved}

    return results
