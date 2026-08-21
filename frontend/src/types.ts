// API types
export interface SearchResult {
  id: string
  headword: string
  transliteration?: string
  pos_tamil?: string
  pos_english?: string
  first_english_def?: string
  first_tamil_def?: string
  sense_count: number
}

export interface Sense {
  id: number
  sense_number: number
  domain?: string
  status: string
  definitions_en: string[]
  definitions_ta: string[]
  examples: Array<{ tamil: string; english?: string; verified: boolean }>
  synonyms: string[]
  antonyms: string[]
  sources: Array<{ title?: string; page_ref?: string; quote?: string }>
  quotations: Array<{ text: string; source?: string; chapter?: string; verse?: string; century?: string; verified: boolean }>
}

export interface WordDetail {
  id: string
  headword: string
  transliteration?: string
  transliteration_iso?: string
  pronunciation_ipa?: string
  pronunciation_audio?: string
  alternate_spellings: string[]
  pos_tamil?: string
  pos_english?: string
  lexical_status: string
  is_compound: boolean
  senses: Sense[]
  morphological_forms: Array<{ form: string; form_type: string; generated: boolean }>
  etymologies: Array<{ etymology: string; language: string; period?: string }>
  community_count: number
  revision: number
  updated_at?: string
}

export interface Contribution {
  id: string
  type: string
  content: string
  explanation?: string
  example?: string
  region?: string
  time_period?: string
  contributor: string
  submitted_at: string
  helpful_count: number
}

export type View = 'search' | 'word' | 'contribute'
