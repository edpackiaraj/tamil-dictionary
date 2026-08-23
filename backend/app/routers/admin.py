"""
Admin router — editorial review queue
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models import Contribution, Word, ZeroResultSearch, WordRequest, Report, Sense, Definition
from fastapi import BackgroundTasks
import gzip
import csv
import io
import asyncio
import uuid
import logging
logger = logging.getLogger(__name__)

router = APIRouter()


class ReviewDecision(BaseModel):
    decision: str   # 'accept' | 'reject' | 'request_evidence' | 'mark_disputed'
    editor_note: Optional[str] = None


@router.get("/queue")
async def get_review_queue(db: AsyncSession = Depends(get_db)):
    """Editorial review queue — all pending contributions"""
    stmt = (
        select(Contribution)
        .where(Contribution.status == "submitted")
        .order_by(Contribution.submitted_at)
        .limit(100)
    )
    items = (await db.execute(stmt)).scalars().all()

    pending_reports = (await db.execute(
        select(func.count()).where(Report.status == "open")
    )).scalar_one()

    word_requests = (await db.execute(
        select(func.count()).where(WordRequest.status == "open")
    )).scalar_one()

    zero_results = (await db.execute(
        select(ZeroResultSearch).order_by(ZeroResultSearch.count.desc()).limit(20)
    )).scalars().all()

    return {
        "stats": {
            "pending_contributions": len(items),
            "open_reports": pending_reports,
            "word_requests": word_requests,
        },
        "zero_result_queries": [
            {"query": z.query, "count": z.count} for z in zero_results
        ],
        "contributions": [
            {
                "id": str(c.id),
                "word_id": c.word_id,
                "type": c.type,
                "content": c.content,
                "explanation": c.explanation,
                "region": c.region,
                "source_ref": c.source_ref,
                "submitted_at": c.submitted_at.isoformat(),
                "helpful_count": c.helpful_count,
            }
            for c in items
        ]
    }


@router.post("/review/{contribution_id}")
async def review_contribution(
    contribution_id: str,
    body: ReviewDecision,
    db: AsyncSession = Depends(get_db),
):
    contrib = await db.get(Contribution, uuid.UUID(contribution_id))
    if not contrib:
        raise HTTPException(404, "Contribution not found")

    decision_map = {
        "accept":           "published",
        "reject":           "rejected",
        "request_evidence": "flagged",
        "mark_disputed":    "flagged",
    }
    new_status = decision_map.get(body.decision)
    if not new_status:
        raise HTTPException(400, "Invalid decision")

    contrib.status = new_status
    contrib.editor_note = body.editor_note
    await db.commit()
    return {"id": contribution_id, "new_status": new_status}


@router.get("/word-requests")
async def get_word_requests(db: AsyncSession = Depends(get_db)):
    stmt = select(WordRequest).where(WordRequest.status == "open") \
        .order_by(WordRequest.request_count.desc()).limit(50)
    items = (await db.execute(stmt)).scalars().all()
    return [
        {"id": i.id, "word": i.word, "suggested_meaning": i.suggested_meaning,
         "count": i.request_count} for i in items
    ]


@router.get("/reports")
async def get_reports(db: AsyncSession = Depends(get_db)):
    stmt = select(Report).where(Report.status == "open").order_by(Report.created_at)
    items = (await db.execute(stmt)).scalars().all()
    return [
        {"id": i.id, "contribution_id": str(i.contribution_id),
         "reason": i.reason, "created_at": i.created_at.isoformat()}
        for i in items
    ]


class IngestionState(BaseModel):
    is_running: bool = False
    total_processed: int = 0
    total_inserted: int = 0
    error: Optional[str] = None
    completed: bool = False

ingestion_state = IngestionState()


async def _ingest_csv_task():
    logger.info("Starting CSV ingestion background task...")
    import os
    import datetime
    from app.database import AsyncSessionLocal
    from sqlalchemy.dialects.postgresql import insert
    
    global ingestion_state

    # The lock was already acquired by start_ingestion, which set is_running = True.
    # We do NOT return here!
    
    ingestion_state.total_processed = 0
    ingestion_state.total_inserted = 0
    ingestion_state.error = None
    ingestion_state.completed = False
    
    # Use absolute path relative to this router file (backend/app/routers/admin.py)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(base_dir, "data", "tamil_dictionary_full.csv.gz")
    if not os.path.exists(csv_path):
        err = f"CSV not found at {csv_path}"
        logger.error(err)
        ingestion_state.error = err
        ingestion_state.is_running = False
        return

    try:
        with gzip.open(csv_path, "rt", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            batch_words = []
            batch_senses = []
            batch_defs = []
            words_inserted = 0
            words_processed = 0
            from app.database import engine
            
            logger.info("Attempting to connect to database for ingestion...")
            async with engine.connect() as conn:
                logger.info("Connected to database successfully! Starting batch processing...")
                for row in reader:
                    words_processed += 1
                    word_id = f"TA-EXT-{uuid.uuid5(uuid.NAMESPACE_URL, row['word'])}"
                    sense_id = f"SENSE-{word_id}"
                    now = datetime.datetime.utcnow()
                    
                    batch_words.append({
                        "id": word_id,
                        "headword": row["word"],
                        "headword_normalized": row["word"],
                        "lexical_status": "published",
                        "is_compound": False,
                        "is_proper_noun": False,
                        "revision": 1,
                        "created_at": now,
                        "updated_at": now
                    })
                    
                    batch_senses.append({
                        "id": sense_id,
                        "word_id": word_id,
                        "sense_number": 1,
                        "status": "published",
                        "created_at": now,
                        "updated_at": now
                    })
                    
                    if row.get("meaning_english"):
                        batch_defs.append({
                            "sense_id": sense_id,
                            "language": "en",
                            "definition": row["meaning_english"],
                            "sort_order": 0
                        })
                        
                    if row.get("meaning_tamil"):
                        batch_defs.append({
                            "sense_id": sense_id,
                            "language": "ta",
                            "definition": row["meaning_tamil"],
                            "sort_order": 1
                        })
                    
                    if len(batch_words) >= 5000:
                        word_stmt = insert(Word).on_conflict_do_nothing(index_elements=["id"])
                        sense_stmt = insert(Sense).on_conflict_do_nothing(index_elements=["id"])
                        def_stmt = insert(Definition).on_conflict_do_nothing(index_elements=["sense_id", "language"])
                        
                        await conn.execute(word_stmt, batch_words)
                        await conn.execute(sense_stmt, batch_senses)
                        if batch_defs:
                            await conn.execute(def_stmt, batch_defs)
                        await conn.commit()
                        words_inserted += len(batch_words)
                        ingestion_state.total_inserted = words_inserted
                        ingestion_state.total_processed = words_processed
                        batch_words, batch_senses, batch_defs = [], [], []
                        await asyncio.sleep(0.05)
                
                if batch_words:
                    word_stmt = insert(Word).on_conflict_do_nothing(index_elements=["id"])
                    sense_stmt = insert(Sense).on_conflict_do_nothing(index_elements=["id"])
                    def_stmt = insert(Definition).on_conflict_do_nothing(index_elements=["sense_id", "language"])
                    
                    await conn.execute(word_stmt, batch_words)
                    await conn.execute(sense_stmt, batch_senses)
                    if batch_defs:
                        await conn.execute(def_stmt, batch_defs)
                    await conn.commit()
                    words_inserted += len(batch_words)
                    ingestion_state.total_inserted = words_inserted
                    ingestion_state.total_processed = words_processed
                    
        logger.info(f"Ingestion complete! Inserted {words_inserted} words.")
        ingestion_state.completed = True
    except Exception as e:
        import traceback
        err_str = f"{repr(e)}\n{traceback.format_exc()}"
        logger.error(f"Ingestion failed: {err_str}")
        ingestion_state.error = err_str
    finally:
        ingestion_state.is_running = False


@router.post("/ingest")
async def ingest_dictionary():
    if ingestion_state.is_running:
        return {"status": "already_running", "message": "An ingestion is currently in progress."}
    
    ingestion_state.is_running = True
    ingestion_state.error = None
    ingestion_state.total_processed = 0
    ingestion_state.total_inserted = 0
    ingestion_state.completed = False
    
    import asyncio
    asyncio.create_task(_ingest_csv_task())
    return {"status": "ingestion_started", "message": "Check server logs or /admin/ingest/status for progress."}


@router.get("/ingest/status")
async def get_ingest_status():
    return ingestion_state.dict()
