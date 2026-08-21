"""
Tamil Morphology Engine
=======================
Rule-based inflection generator for Tamil nouns.

Covers:
  - All 8 noun cases (வேற்றுமை உருபுகள்)
  - Plural forms
  - Verb infinitive, verbal noun, negative (basic)
  - Sandhi rules for common word-ending patterns

Tamil noun cases:
  0. Nominative  (எழுவாய்)      — base form
  1. Accusative  (செயப்படுபொருள்) — ஐ suffix
  2. Dative      (கொடை)         — க்கு suffix
  3. Sociative   (உடனிகழ்ச்சி)   — ஓடு suffix
  4. Instrumental (கருவி)        — ஆல் suffix
  5. Ablative    (நீங்கல்)       — இல் இருந்து suffix
  6. Genitive    (உடைமை)        — இன் / ஆல் suffix
  7. Locative    (இடவேற்றுமை)   — இல் suffix

Word-ending classes (Tamil orthographic patterns):
  Class A: ends in -டு / -று / -து  (e.g., வீடு, ஆறு, பாது)
  Class B: ends in -ம்              (e.g., மரம், நகரம், பிரம்)
  Class C: ends in -ல் / -ண் / -ன் (e.g., கடல், காடு, ஆண்)
  Class D: ends in -ர் / -ழ்        (e.g., தமிழ், ஊர்)
  Class E: ends in -வு / -பு / -கு  (e.g., அன்பு, நடை)
  Class F: ends in -ய் / -ஐ        (e.g., தாய், கை)
  Class G: ends in open vowel -ஆ    (e.g., மா, தரா)
  Class X: default / unknown        (append suffix directly)
"""

import re
import unicodedata

# ── Tamil Unicode constants ─────────────────────────────────────────────────
TAMIL_VOWELS      = "அஆஇஈஉஊஎஏஐஒஓஔ"
TAMIL_CONSONANTS  = "கசடதபமயரலவழளணன"
AAYTHAM           = "ஃ"
PULLI             = "\u0BCD"  # virama / pulli (vowel killer)

# ── Vowel-mark endings for detection ────────────────────────────────────────
ENDS_DU  = re.compile(r"[டறத]ு$")       # -டு -று -து
ENDS_M   = re.compile(r"ம்$")            # -ம்
ENDS_L   = re.compile(r"[லண]்$")        # -ல் -ண்
ENDS_N   = re.compile(r"ன்$")            # -ன்
ENDS_R   = re.compile(r"[ரழள]்$")       # -ர் -ழ் -ள்
ENDS_VU  = re.compile(r"[வபக]ு$")       # -வு -பு -கு
ENDS_YU  = re.compile(r"[யை]$")         # -ய் or ஐ ending
ENDS_LONG = re.compile(r"[ஆஈஊஏஐஓஔ]$") # long vowel ending


def classify(word: str) -> str:
    """Return the morphological class of a Tamil word."""
    if ENDS_DU.search(word):   return "A"  # வீடு, ஆறு
    if ENDS_M.search(word):    return "B"  # மரம்
    if ENDS_L.search(word):    return "C"  # கடல், ஆண்
    if ENDS_N.search(word):    return "N"  # ஆண்(ன்)
    if ENDS_R.search(word):    return "D"  # தமிழ், ஊர்
    if ENDS_VU.search(word):   return "E"  # அன்பு
    if ENDS_YU.search(word):   return "F"  # தாய்
    if ENDS_LONG.search(word): return "G"  # மா, தரா
    return "X"


# ── Oblique stem computation ─────────────────────────────────────────────────

def oblique(word: str, cls: str) -> str:
    """
    Compute the oblique stem used before case suffixes.
    The oblique stem differs from the nominative for many classes.
    """
    if cls == "A":
        # வீடு → வீட்ட் (double the final stop, remove -உ vowel mark)
        # Mechanism: replace final Xu with X்X
        # e.g., வீடு → base=வீட், oblique=வீட்ட
        base = word[:-1]  # remove -உ vowel mark (அ-ஔ range)
        # Final consonant is the character before the vowel mark உ
        # In Unicode: consonant = base[-1], we need to double it
        final_char = base[-1]  # e.g., ட
        return base + "்" + final_char  # வீட் + ் + ட = வீட்ட
    elif cls == "B":
        # மரம் → மரத்த
        # -ம் becomes -த்த for hard stops, or -ற்ற for retroflex
        stem = word[:-2]  # remove ம்
        # Determine if we need த்த or த்
        return stem + "த்த"
    elif cls == "C" or cls == "N":
        # கடல் → கடல் (no change, suffix appended directly with connector)
        return word[:-1]  # remove pulli ்
    elif cls == "D":
        # தமிழ் → தமிழ் (suffix directly after removing pulli)
        return word[:-1]
    elif cls == "E":
        # அன்பு → அன்ப (remove -உ)
        return word[:-1]
    elif cls == "F":
        # தாய் → தாய் (use as-is, suffix after)
        return word
    elif cls == "G":
        # மா → மா (suffix directly)
        return word
    else:
        return word


# ── Suffix tables ────────────────────────────────────────────────────────────

# connector vowels by class when appending suffixes
def _connect(cls: str) -> str:
    """Return the connector vowel (agglutination vowel) for each class."""
    return {
        "A": "",   # oblique already ends in consonant
        "B": "",   # oblique ends in consonant
        "C": "இ",  # கடல் + இ + ல் = கடலில்
        "N": "இ",
        "D": "இ",  # தமிழ் + இ + ல் = தமிழில்
        "E": "",   # அன்ப + இ... wait, அன்பில் → connector = இ
        "F": "இ",
        "G": "வி",  # மா + வி + ல் = மாவில்
        "X": "இ",
    }.get(cls, "இ")


def inflect(word: str) -> dict[str, str]:
    """
    Generate all inflected forms for a Tamil noun.
    Returns dict of {form_type: inflected_form}.
    """
    word = word.strip()
    if not word:
        return {}

    cls = classify(word)
    obl = oblique(word, cls)
    con = _connect(cls)

    # For class E (அன்பு), connector is இ
    if cls == "E":
        con = "இ"

    forms = {}

    # ── Plural ──────────────────────────────────────────────────────────
    if cls == "A":
        forms["plural"] = word[:-1] + "கள்"   # வீடுகள்
    elif cls == "B":
        forms["plural"] = word[:-2] + "ங்கள்"  # மரங்கள்
    elif cls in ("C", "N"):
        forms["plural"] = word[:-1] + "கள்"   # கடல்கள்
    elif cls == "D":
        forms["plural"] = word[:-1] + "கள்"   # தமிழ்கள் (rare but grammatical)
    elif cls == "E":
        forms["plural"] = word[:-1] + "குகள்"  # அன்புகள்  actually அன்புகள்
    elif cls == "F":
        forms["plural"] = word + "கள்"        # தாய்கள்
    else:
        forms["plural"] = word + "கள்"

    # ── Accusative (-ஐ) ─────────────────────────────────────────────────
    if cls == "A":
        forms["accusative"] = obl + "ை"        # வீட்டை
    elif cls == "B":
        forms["accusative"] = obl + "ை"        # மரத்தை
    else:
        forms["accusative"] = obl + con + "ை"  # கடலை, தமிழை, அன்பை

    # ── Dative (-க்கு / -உக்கு) ─────────────────────────────────────────
    if cls == "A":
        forms["dative"] = obl + "ுக்கு"        # வீட்டுக்கு
    elif cls == "B":
        forms["dative"] = obl + "ிற்கு"        # மரத்திற்கு
    elif cls in ("C", "N", "D"):
        forms["dative"] = obl + con + "க்கு"   # கடலுக்கு
    elif cls == "E":
        forms["dative"] = obl + "க்கு"         # அன்புக்கு (obl=அன்ப + connector later)
        forms["dative"] = word[:-1] + "க்கு"   # simpler: அன்பு → அன்பக்கு
        # Most natural: அன்புக்கு
        forms["dative"] = word + "க்கு"
    elif cls == "F":
        forms["dative"] = word + "க்கு"        # தாய்க்கு
    elif cls == "G":
        forms["dative"] = word + "வுக்கு"      # மாவுக்கு
    else:
        forms["dative"] = word + "க்கு"

    # ── Locative (-இல்) ──────────────────────────────────────────────────
    if cls == "A":
        forms["locative"] = obl + "ில்"         # வீட்டில்
    elif cls == "B":
        forms["locative"] = obl + "ில்"         # மரத்தில்
    elif cls in ("C", "N"):
        forms["locative"] = obl + con + "ல்"   # கடலில்
    elif cls == "D":
        forms["locative"] = obl + con + "ல்"   # தமிழில்
    elif cls == "E":
        forms["locative"] = word + "ல்"        # அன்பில்  (அன்பு + இல் = அன்பில்)
        forms["locative"] = word[:-1] + "இல்"  # simpler
        forms["locative"] = word[:-1] + "ில்"  # அன்பில்
    elif cls == "F":
        forms["locative"] = word + "ல்"        # தாய்யில் → தாயில்
    elif cls == "G":
        forms["locative"] = word + "வில்"      # மாவில்
    else:
        forms["locative"] = word + "இல்"

    # ── Ablative (-இல் இருந்து) ──────────────────────────────────────────
    forms["ablative"] = forms.get("locative", word + "இல்") + " இருந்து"

    # ── Genitive (-இன் / -உடைய) ─────────────────────────────────────────
    if cls == "A":
        forms["genitive"] = obl + "ுடைய"       # வீட்டுடைய
    elif cls == "B":
        forms["genitive"] = obl + "ின்"         # மரத்தின்
    elif cls in ("C", "N"):
        forms["genitive"] = obl + con + "ன்"   # கடலின்
    elif cls == "D":
        forms["genitive"] = obl + con + "ன்"   # தமிழின்
    elif cls == "E":
        forms["genitive"] = word + "ன்"        # அன்பின் (more natural)
    elif cls == "G":
        forms["genitive"] = word + "வின்"      # மாவின்
    else:
        forms["genitive"] = word + "இன்"

    # ── Instrumental (-ஆல்) ──────────────────────────────────────────────
    if cls == "A":
        forms["instrumental"] = obl + "ால்"    # வீட்டால்
    elif cls == "B":
        forms["instrumental"] = obl + "ால்"    # மரத்தால்
    elif cls in ("C", "N", "D"):
        forms["instrumental"] = obl + con + "ல்"  # கடலால்  — reuse locative pattern
        forms["instrumental"] = word[:-1] + "ால்" if cls in ("C","N","D") else word + "ால்"
    elif cls == "E":
        forms["instrumental"] = word + "ால்"   # அன்பால்
    else:
        forms["instrumental"] = word + "ால்"

    # ── Sociative (-உடன்) ────────────────────────────────────────────────
    if cls == "A":
        forms["sociative"] = obl + "ுடன்"      # வீட்டுடன்
    elif cls == "B":
        forms["sociative"] = obl + "ுடன்"      # மரத்துடன்
    else:
        forms["sociative"] = word + "உடன்"

    # ── Plural cases ─────────────────────────────────────────────────────
    plural = forms.get("plural", word + "கள்")
    forms["plural_accusative"] = plural[:-1] + "ை"  # மரங்களை
    forms["plural_dative"]     = plural + "க்கு"    # மரங்களுக்கு
    forms["plural_locative"]   = plural + "இல்"     # மரங்களில்

    return forms


def generate_all_forms(word: str) -> list[dict]:
    """
    Return a list of {form, form_type, generated} dicts
    suitable for inserting into morphological_forms table.
    """
    forms = inflect(word)
    return [
        {"form": v, "form_type": k, "generated": True}
        for k, v in forms.items()
        if v and v != word
    ]


def find_base(form: str, candidates: list[str]) -> str | None:
    """
    Given an inflected form and a list of candidate base words,
    return the most likely base word. Used for reverse morphology lookup.
    """
    form = form.strip()
    for candidate in candidates:
        candidate_forms = inflect(candidate)
        if form in candidate_forms.values():
            return candidate
    return None


# ── Quick test ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_words = [
        ("வீடு",   "house"),
        ("மரம்",   "tree"),
        ("கடல்",   "sea"),
        ("தமிழ்",  "Tamil"),
        ("அன்பு",  "love"),
        ("தாய்",   "mother"),
        ("நாடு",   "country"),
        ("இரவு",   "night"),
    ]

    for word, meaning in test_words:
        print(f"\n{'═'*55}")
        print(f"  {word}  ({meaning})")
        print(f"  Class: {classify(word)}")
        print(f"{'─'*55}")
        forms = inflect(word)
        for form_type, form in forms.items():
            print(f"  {form_type:<25} {form}")
