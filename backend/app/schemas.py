"""Pydantic response schemas"""
from pydantic import BaseModel
from typing import Optional, List, Any


class SearchResultItem(BaseModel):
    id: str
    headword: str
    transliteration: Optional[str]
    pos_tamil: Optional[str]
    pos_english: Optional[str]
    first_english_def: Optional[str]
    first_tamil_def: Optional[str]
    sense_count: int


class SearchResponse(BaseModel):
    query: str
    total: int
    results: List[SearchResultItem]


class SenseDetail(BaseModel):
    id: str
    sense_number: int
    domain: Optional[str]
    status: str
    definitions_en: List[str]
    definitions_ta: List[str]
    examples: List[dict]
    synonyms: List[str]
    antonyms: List[str]
    sources: List[dict]
    quotations: List[dict]


class WordDetail(BaseModel):
    id: str
    headword: str
    transliteration: Optional[str]
    transliteration_iso: Optional[str]
    pronunciation_ipa: Optional[str]
    pronunciation_audio: Optional[str]
    alternate_spellings: List[str]
    pos_tamil: Optional[str]
    pos_english: Optional[str]
    lexical_status: str
    is_compound: bool
    senses: List[SenseDetail]
    morphological_forms: List[dict]
    etymologies: List[dict]
    community_count: int
    revision: int
    updated_at: Optional[str]
