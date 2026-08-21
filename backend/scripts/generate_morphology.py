"""
Morphology batch generator script
Run this after importing words to pre-generate all inflected forms.

Usage:
    python scripts/generate_morphology.py

This makes inflected form search instant instead of on-demand.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Word, MorphologicalForm
from app.morphology import generate_all_forms, classify


async def main():
    async with AsyncSessionLocal() as db:
        # Get all published words without morphological forms
        stmt = (
            select(Word)
            .where(Word.lexical_status == "published")
            .outerjoin(MorphologicalForm, MorphologicalForm.word_id == Word.id)
            .where(MorphologicalForm.id == None)  # only words with no forms yet
        )
        words = (await db.execute(stmt)).scalars().all()
        print(f"Found {len(words)} words needing morphological forms")

        saved_total = 0
        for word in words:
            forms = generate_all_forms(word.headword)
            cls = classify(word.headword)
            print(f"  [{cls}] {word.headword} → {len(forms)} forms")

            for g in forms:
                try:
                    db.add(MorphologicalForm(
                        word_id=word.id,
                        form=g["form"],
                        form_type=g["form_type"],
                        generated=True,
                    ))
                    saved_total += 1
                except Exception:
                    pass

            try:
                await db.commit()
            except Exception as e:
                print(f"    [ERROR] {e}")
                await db.rollback()

        print(f"\n✅ Done. Generated {saved_total} morphological forms total.")


if __name__ == "__main__":
    asyncio.run(main())
