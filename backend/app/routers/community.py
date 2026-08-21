"""
Community router — contributions, votes, reports, word requests
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models import Contribution, ContributionVote, Report, WordRequest, Word

router = APIRouter()

CONTRIBUTION_TYPES = [
    "additional_meaning", "regional_meaning", "modern_usage",
    "correction", "new_word", "example", "pronunciation",
    "translation", "source", "spelling", "other"
]


class ContributionCreate(BaseModel):
    word_id: Optional[str] = None
    sense_id: Optional[int] = None
    type: str
    content: str
    explanation: Optional[str] = None
    example: Optional[str] = None
    region: Optional[str] = None
    time_period: Optional[str] = None
    source_ref: Optional[str] = None
    contributor_name: Optional[str] = None  # anonymous display name


class VoteCreate(BaseModel):
    contribution_id: str
    vote: str  # 'helpful' | 'unhelpful' | 'needs_evidence'


class ReportCreate(BaseModel):
    contribution_id: str
    reason: str


class WordRequestCreate(BaseModel):
    word: str
    suggested_meaning: Optional[str] = None


@router.post("/contribute", status_code=201)
async def submit_contribution(
    body: ContributionCreate,
    db: AsyncSession = Depends(get_db),
):
    if body.type not in CONTRIBUTION_TYPES:
        raise HTTPException(400, f"Invalid type. Must be one of: {CONTRIBUTION_TYPES}")

    if not body.content.strip():
        raise HTTPException(400, "Content cannot be empty")

    # Verify word exists if word_id provided
    if body.word_id:
        word = await db.get(Word, body.word_id)
        if not word:
            raise HTTPException(404, "Word not found")

    contribution = Contribution(
        word_id=body.word_id,
        sense_id=body.sense_id,
        type=body.type,
        content=body.content.strip(),
        explanation=body.explanation,
        example=body.example,
        region=body.region,
        time_period=body.time_period,
        source_ref=body.source_ref,
        status="submitted",  # never auto-published
    )
    db.add(contribution)
    await db.commit()
    await db.refresh(contribution)
    return {"id": str(contribution.id), "status": "submitted",
            "message": "உங்கள் பங்களிப்பு பெறப்பட்டது. ஆசிரியர் மதிப்பாய்வுக்குப் பிறகு வெளியிடப்படும்."}


@router.post("/vote")
async def vote_contribution(body: VoteCreate, db: AsyncSession = Depends(get_db)):
    if body.vote not in ("helpful", "unhelpful", "needs_evidence"):
        raise HTTPException(400, "Invalid vote type")

    contrib = await db.get(Contribution, uuid.UUID(body.contribution_id))
    if not contrib:
        raise HTTPException(404, "Contribution not found")

    if body.vote == "helpful":
        contrib.helpful_count += 1
        await db.commit()

    return {"status": "ok"}


@router.post("/report")
async def report_contribution(body: ReportCreate, db: AsyncSession = Depends(get_db)):
    contrib = await db.get(Contribution, uuid.UUID(body.contribution_id))
    if not contrib:
        raise HTTPException(404, "Contribution not found")

    report = Report(
        contribution_id=contrib.id,
        reason=body.reason,
        status="open",
    )
    db.add(report)
    await db.commit()
    return {"status": "reported"}


@router.post("/request-word", status_code=201)
async def request_word(body: WordRequestCreate, db: AsyncSession = Depends(get_db)):
    word = body.word.strip()
    if not word:
        raise HTTPException(400, "Word cannot be empty")

    stmt = select(WordRequest).where(WordRequest.word == word)
    existing = (await db.execute(stmt)).scalar_one_or_none()

    if existing:
        existing.request_count += 1
        await db.commit()
        return {"status": "updated", "request_count": existing.request_count}
    else:
        wr = WordRequest(word=word, suggested_meaning=body.suggested_meaning)
        db.add(wr)
        await db.commit()
        return {"status": "created", "request_count": 1}
