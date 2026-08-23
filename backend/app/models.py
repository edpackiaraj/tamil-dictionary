"""
SQLAlchemy ORM models — mirrors database/schema.sql
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime, ForeignKey,
    UniqueConstraint, ARRAY, Index
)
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PartOfSpeech(Base):
    __tablename__ = "parts_of_speech"
    id:            Mapped[int]  = mapped_column(Integer, primary_key=True)
    code:          Mapped[str]  = mapped_column(String, unique=True)
    tamil_label:   Mapped[str]  = mapped_column(Text)
    english_label: Mapped[str]  = mapped_column(Text)
    sort_order:    Mapped[int]  = mapped_column(Integer, default=0)


class UsageLabel(Base):
    __tablename__ = "usage_labels"
    id:            Mapped[int] = mapped_column(Integer, primary_key=True)
    code:          Mapped[str] = mapped_column(String, unique=True)
    tamil_label:   Mapped[str] = mapped_column(Text)
    english_label: Mapped[str] = mapped_column(Text)
    category:      Mapped[str] = mapped_column(String)


class Word(Base):
    __tablename__ = "words"
    id:                  Mapped[str]           = mapped_column(String, primary_key=True)
    headword:            Mapped[str]           = mapped_column(Text, nullable=False)
    headword_normalized: Mapped[str]           = mapped_column(Text, nullable=False)
    alternate_spellings: Mapped[Optional[list]] = mapped_column(ARRAY(Text))
    transliteration:     Mapped[Optional[str]] = mapped_column(Text)
    transliteration_iso: Mapped[Optional[str]] = mapped_column(Text)
    pronunciation_ipa:   Mapped[Optional[str]] = mapped_column(Text)
    pronunciation_audio: Mapped[Optional[str]] = mapped_column(Text)
    part_of_speech_id:   Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("parts_of_speech.id"))
    lexical_status:      Mapped[str]           = mapped_column(String, default="published")
    is_compound:         Mapped[bool]          = mapped_column(Boolean, default=False)
    is_proper_noun:      Mapped[bool]          = mapped_column(Boolean, default=False)
    frequency_rank:      Mapped[Optional[int]] = mapped_column(Integer)
    created_at:          Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())
    updated_at:          Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())
    created_by:          Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True))
    revision:            Mapped[int]           = mapped_column(Integer, default=1)

    part_of_speech:   Mapped[Optional[PartOfSpeech]] = relationship("PartOfSpeech", lazy="joined")
    senses:           Mapped[List["Sense"]]           = relationship("Sense", back_populates="word", order_by="Sense.sense_number", lazy="select")
    morphological_forms: Mapped[List["MorphologicalForm"]] = relationship("MorphologicalForm", lazy="select")
    etymologies:      Mapped[List["Etymology"]]       = relationship("Etymology", lazy="select")
    related_from:     Mapped[List["RelatedWord"]]     = relationship("RelatedWord", foreign_keys="RelatedWord.word_id", lazy="select")


class Sense(Base):
    __tablename__ = "senses"
    id:                Mapped[str]           = mapped_column(String, primary_key=True)
    word_id:           Mapped[str]           = mapped_column(String, ForeignKey("words.id", ondelete="CASCADE"))
    sense_number:      Mapped[int]           = mapped_column(Integer)
    part_of_speech_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("parts_of_speech.id"))
    domain:            Mapped[Optional[str]] = mapped_column(Text)
    status:            Mapped[str]           = mapped_column(String, default="published")
    created_at:        Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())
    updated_at:        Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())

    __table_args__ = (UniqueConstraint("word_id", "sense_number"),)

    word:          Mapped["Word"]              = relationship("Word", back_populates="senses")
    definitions:   Mapped[List["Definition"]] = relationship("Definition", lazy="joined", order_by="Definition.sort_order")
    examples:      Mapped[List["Example"]]    = relationship("Example", lazy="select", order_by="Example.sort_order")
    synonyms:      Mapped[List["Synonym"]]    = relationship("Synonym", lazy="select", order_by="Synonym.sort_order")
    antonyms:      Mapped[List["Antonym"]]    = relationship("Antonym", lazy="select", order_by="Antonym.sort_order")
    sources:       Mapped[List["SenseSource"]] = relationship("SenseSource", lazy="select")
    quotations:    Mapped[List["Quotation"]]  = relationship("Quotation", lazy="select")


class Definition(Base):
    __tablename__ = "definitions"
    id:         Mapped[int] = mapped_column(Integer, primary_key=True)
    sense_id:   Mapped[str] = mapped_column(String, ForeignKey("senses.id", ondelete="CASCADE"))
    language:   Mapped[str] = mapped_column(String(2))
    definition: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (UniqueConstraint("sense_id", "language"),)

    sense: Mapped["Sense"] = relationship("Sense", back_populates="definitions")


class Example(Base):
    __tablename__ = "examples"
    id:              Mapped[int]           = mapped_column(Integer, primary_key=True)
    sense_id:        Mapped[str]           = mapped_column(String, ForeignKey("senses.id", ondelete="CASCADE"))
    example_tamil:   Mapped[str]           = mapped_column(Text)
    example_english: Mapped[Optional[str]] = mapped_column(Text)
    source_work_id:  Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("source_works.id"))
    verified:        Mapped[bool]          = mapped_column(Boolean, default=False)
    sort_order:      Mapped[int]           = mapped_column(Integer, default=0)


class Synonym(Base):
    __tablename__ = "synonyms"
    id:          Mapped[int]           = mapped_column(Integer, primary_key=True)
    sense_id:    Mapped[str]           = mapped_column(String, ForeignKey("senses.id", ondelete="CASCADE"))
    synonym:     Mapped[str]           = mapped_column(Text)
    word_id_ref: Mapped[Optional[str]] = mapped_column(String, ForeignKey("words.id"))
    sort_order:  Mapped[int]           = mapped_column(Integer, default=0)


class Antonym(Base):
    __tablename__ = "antonyms"
    id:          Mapped[int]           = mapped_column(Integer, primary_key=True)
    sense_id:    Mapped[str]           = mapped_column(String, ForeignKey("senses.id", ondelete="CASCADE"))
    antonym:     Mapped[str]           = mapped_column(Text)
    word_id_ref: Mapped[Optional[str]] = mapped_column(String, ForeignKey("words.id"))
    sort_order:  Mapped[int]           = mapped_column(Integer, default=0)


class RelatedWord(Base):
    __tablename__ = "related_words"
    id:              Mapped[int] = mapped_column(Integer, primary_key=True)
    word_id:         Mapped[str] = mapped_column(String, ForeignKey("words.id", ondelete="CASCADE"))
    related_word_id: Mapped[str] = mapped_column(String, ForeignKey("words.id", ondelete="CASCADE"))
    relation_type:   Mapped[str] = mapped_column(String)
    __table_args__ = (UniqueConstraint("word_id", "related_word_id", "relation_type"),)


class MorphologicalForm(Base):
    __tablename__ = "morphological_forms"
    id:        Mapped[int]  = mapped_column(Integer, primary_key=True)
    word_id:   Mapped[str]  = mapped_column(String, ForeignKey("words.id", ondelete="CASCADE"))
    form:      Mapped[str]  = mapped_column(Text)
    form_type: Mapped[str]  = mapped_column(Text)
    generated: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("word_id", "form_type"),)


class Etymology(Base):
    __tablename__ = "etymologies"
    id:        Mapped[int]           = mapped_column(Integer, primary_key=True)
    word_id:   Mapped[str]           = mapped_column(String, ForeignKey("words.id", ondelete="CASCADE"))
    etymology: Mapped[str]           = mapped_column(Text)
    language:  Mapped[str]           = mapped_column(String, default="en")
    period:    Mapped[Optional[str]] = mapped_column(Text)
    notes:     Mapped[Optional[str]] = mapped_column(Text)


class SourceWork(Base):
    __tablename__ = "source_works"
    id:               Mapped[int]           = mapped_column(Integer, primary_key=True)
    title:            Mapped[str]           = mapped_column(Text)
    title_tamil:      Mapped[Optional[str]] = mapped_column(Text)
    author:           Mapped[Optional[str]] = mapped_column(Text)
    year:             Mapped[Optional[int]] = mapped_column(Integer)
    publisher:        Mapped[Optional[str]] = mapped_column(Text)
    url:              Mapped[Optional[str]] = mapped_column(Text)
    license:          Mapped[Optional[str]] = mapped_column(Text)
    copyright_status: Mapped[Optional[str]] = mapped_column(Text)
    attribution:      Mapped[Optional[str]] = mapped_column(Text)
    may_reproduce:    Mapped[bool]          = mapped_column(Boolean, default=False)
    notes:            Mapped[Optional[str]] = mapped_column(Text)


class SenseSource(Base):
    __tablename__ = "sense_sources"
    id:             Mapped[int]           = mapped_column(Integer, primary_key=True)
    sense_id:       Mapped[str]           = mapped_column(String, ForeignKey("senses.id", ondelete="CASCADE"))
    source_work_id: Mapped[int]           = mapped_column(Integer, ForeignKey("source_works.id"))
    page_ref:       Mapped[Optional[str]] = mapped_column(Text)
    quote:          Mapped[Optional[str]] = mapped_column(Text)
    source_work:    Mapped["SourceWork"]  = relationship("SourceWork", lazy="joined")


class Quotation(Base):
    __tablename__ = "quotations"
    id:                        Mapped[int]           = mapped_column(Integer, primary_key=True)
    sense_id:                  Mapped[str]           = mapped_column(String, ForeignKey("senses.id", ondelete="CASCADE"))
    quotation_tamil:           Mapped[str]           = mapped_column(Text)
    quotation_transliteration: Mapped[Optional[str]] = mapped_column(Text)
    source_work_id:            Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("source_works.id"))
    chapter:                   Mapped[Optional[str]] = mapped_column(Text)
    verse:                     Mapped[Optional[str]] = mapped_column(Text)
    century:                   Mapped[Optional[str]] = mapped_column(Text)
    verified:                  Mapped[bool]          = mapped_column(Boolean, default=False)
    source_work:               Mapped[Optional["SourceWork"]] = relationship("SourceWork", lazy="joined")


class User(Base):
    __tablename__ = "users"
    id:             Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name:   Mapped[str]       = mapped_column(Text)
    email:          Mapped[str]       = mapped_column(Text, unique=True)
    email_verified: Mapped[bool]      = mapped_column(Boolean, default=False)
    password_hash:  Mapped[str]       = mapped_column(Text)
    role:           Mapped[str]       = mapped_column(String, default="contributor")
    is_active:      Mapped[bool]      = mapped_column(Boolean, default=True)
    joined_at:      Mapped[datetime]  = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())
    last_seen:      Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Contribution(Base):
    __tablename__ = "contributions"
    id:             Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    word_id:        Mapped[Optional[str]]  = mapped_column(String, ForeignKey("words.id"))
    sense_id:       Mapped[Optional[str]]  = mapped_column(String, ForeignKey("senses.id"))
    contributor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    type:           Mapped[str]         = mapped_column(String)
    content:        Mapped[str]         = mapped_column(Text)
    explanation:    Mapped[Optional[str]] = mapped_column(Text)
    example:        Mapped[Optional[str]] = mapped_column(Text)
    region:         Mapped[Optional[str]] = mapped_column(Text)
    time_period:    Mapped[Optional[str]] = mapped_column(Text)
    source_ref:     Mapped[Optional[str]] = mapped_column(Text)
    status:         Mapped[str]         = mapped_column(String, default="submitted")
    editor_note:    Mapped[Optional[str]] = mapped_column(Text)
    reviewed_by:    Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_at:    Mapped[Optional[datetime]]  = mapped_column(DateTime(timezone=True))
    submitted_at:   Mapped[datetime]    = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())
    helpful_count:  Mapped[int]         = mapped_column(Integer, default=0)

    contributor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[contributor_id], lazy="joined")


class Revision(Base):
    __tablename__ = "revisions"
    id:             Mapped[int]           = mapped_column(Integer, primary_key=True)
    entity_type:    Mapped[str]           = mapped_column(Text)
    entity_id:      Mapped[str]           = mapped_column(Text)
    previous_value: Mapped[Optional[dict]] = mapped_column(JSONB)
    new_value:      Mapped[Optional[dict]] = mapped_column(JSONB)
    editor_id:      Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    reason:         Mapped[Optional[str]] = mapped_column(Text)
    created_at:     Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())


class ZeroResultSearch(Base):
    __tablename__ = "zero_result_searches"
    query:    Mapped[str]      = mapped_column(Text, primary_key=True)
    count:    Mapped[int]      = mapped_column(Integer, default=1)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())


class WordRequest(Base):
    __tablename__ = "word_requests"
    id:                Mapped[int]           = mapped_column(Integer, primary_key=True)
    word:              Mapped[str]           = mapped_column(Text, unique=True)
    suggested_meaning: Mapped[Optional[str]] = mapped_column(Text)
    request_count:     Mapped[int]           = mapped_column(Integer, default=1)
    status:            Mapped[str]           = mapped_column(String, default="open")
    created_at:        Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())


class ContributionVote(Base):
    __tablename__ = "contribution_votes"
    id:              Mapped[int]        = mapped_column(Integer, primary_key=True)
    contribution_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contributions.id", ondelete="CASCADE"))
    user_id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    vote:            Mapped[str]       = mapped_column(String)   # 'helpful' | 'unhelpful' | 'needs_evidence'
    created_at:      Mapped[datetime]  = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())
    __table_args__ = (UniqueConstraint("contribution_id", "user_id"),)


class Report(Base):
    __tablename__ = "reports"
    id:              Mapped[int]                   = mapped_column(Integer, primary_key=True)
    contribution_id: Mapped[Optional[uuid.UUID]]  = mapped_column(UUID(as_uuid=True), ForeignKey("contributions.id"))
    reporter_id:     Mapped[Optional[uuid.UUID]]  = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    reason:          Mapped[str]                  = mapped_column(Text)
    status:          Mapped[str]                  = mapped_column(String, default="open")
    created_at:      Mapped[datetime]             = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())


class Discussion(Base):
    __tablename__ = "discussions"
    id:              Mapped[int]                  = mapped_column(Integer, primary_key=True)
    word_id:         Mapped[Optional[str]]        = mapped_column(String, ForeignKey("words.id"))
    contribution_id: Mapped[Optional[uuid.UUID]]  = mapped_column(UUID(as_uuid=True), ForeignKey("contributions.id"))
    body:            Mapped[str]                  = mapped_column(Text)
    author_id:       Mapped[Optional[uuid.UUID]]  = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_closed:       Mapped[bool]                 = mapped_column(Boolean, default=False)
    created_at:      Mapped[datetime]             = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())

    replies: Mapped[List["DiscussionReply"]] = relationship("DiscussionReply", lazy="select")


class DiscussionReply(Base):
    __tablename__ = "discussion_replies"
    id:            Mapped[int]                  = mapped_column(Integer, primary_key=True)
    discussion_id: Mapped[int]                  = mapped_column(Integer, ForeignKey("discussions.id", ondelete="CASCADE"))
    body:          Mapped[str]                  = mapped_column(Text)
    author_id:     Mapped[Optional[uuid.UUID]]  = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at:    Mapped[datetime]             = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())
