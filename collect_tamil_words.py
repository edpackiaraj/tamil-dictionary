"""
Tamil Dictionary Collector
Collects Tamil words + meanings from multiple open corpora.
Stores everything in SQLite: tamil_dictionary.db
Sources:
  1. Tamil Wiktionary XML dump
  2. Kaikki.org pre-extracted Tamil-English dictionary
  3. GitHub: powertamil-dictionary (AgaraMuthali 63k words)
  4. GitHub: tamil-language-words-list
  5. GitHub: Tamil-words-Collections-with-English-Meaning
  6. Open-Tamil solthiruthi word list
  7. Tamil Wikipedia dump (word extraction)
"""

import sqlite3
import requests
import json
import csv
import re
import os
import sys
import time
import gzip
import bz2
import zipfile
import io
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

# ── Config ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DB_PATH  = BASE_DIR / "tamil_dictionary.db"
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

TAMIL_UNICODE_RANGE = re.compile(r'[\u0B80-\u0BFF]')

# ── Database Setup ──────────────────────────────────────────────────────────
def init_db(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS words (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        word            TEXT NOT NULL,
        meaning_tamil   TEXT,
        meaning_english TEXT,
        part_of_speech  TEXT,
        source          TEXT,
        created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_word_source ON words(word, source);
    CREATE INDEX IF NOT EXISTS idx_word ON words(word);
    """)
    conn.commit()
    print("[DB] Initialized sqlite database:", DB_PATH)

def insert_batch(conn, rows):
    """rows: list of (word, meaning_tamil, meaning_english, pos, source)"""
    conn.executemany("""
        INSERT OR IGNORE INTO words (word, meaning_tamil, meaning_english, part_of_speech, source)
        VALUES (?, ?, ?, ?, ?)
    """, rows)
    conn.commit()

def count_words(conn):
    return conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]

# ── Helpers ─────────────────────────────────────────────────────────────────
def is_tamil(text):
    return bool(TAMIL_UNICODE_RANGE.search(str(text)))

def download(url, cache_name, binary=False):
    path = CACHE_DIR / cache_name
    if path.exists():
        print(f"  [cache] {cache_name}")
        return path.read_bytes() if binary else path.read_text(encoding="utf-8", errors="ignore")
    print(f"  [download] {url}")
    try:
        r = requests.get(url, timeout=120, stream=True)
        r.raise_for_status()
        data = r.content
        path.write_bytes(data)
        return data if binary else data.decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None

# ══════════════════════════════════════════════════════════════════════════
# SOURCE 1: Kaikki.org — pre-extracted Tamil Wiktionary (JSONL)
# ══════════════════════════════════════════════════════════════════════════
def collect_kaikki(conn):
    print("\n[1] Kaikki.org — Tamil Wiktionary JSONL")
    url = "https://kaikki.org/dictionary/Tamil/kaikki.org-dictionary-Tamil.json"
    data = download(url, "kaikki_tamil.json")
    if not data:
        # try alternative URL
        url2 = "https://kaikki.org/dictionary/Tamil/by-pos/noun/kaikki.org-dictionary-Tamil-nouns.json"
        data = download(url2, "kaikki_tamil_nouns.json")
    if not data:
        print("  [SKIP] Kaikki not reachable")
        return

    rows = []
    for line in data.strip().splitlines():
        try:
            obj = json.loads(line)
        except:
            continue
        word = obj.get("word", "").strip()
        if not word or not is_tamil(word):
            continue
        pos = obj.get("pos", "")
        en_meanings = []
        for sense in obj.get("senses", []):
            for gl in sense.get("glosses", []):
                if gl:
                    en_meanings.append(gl)
        ta_meanings = []
        for tr in obj.get("translations", []):
            if tr.get("lang_code") == "ta":
                ta_meanings.append(tr.get("word", ""))
        rows.append((
            word,
            "; ".join(ta_meanings) or None,
            "; ".join(en_meanings) or None,
            pos or None,
            "kaikki"
        ))
        if len(rows) >= 1000:
            insert_batch(conn, rows)
            rows = []
    insert_batch(conn, rows)
    print(f"  [DONE] Total DB: {count_words(conn):,}")

# ══════════════════════════════════════════════════════════════════════════
# SOURCE 2: Tamil Wiktionary XML dump
# ══════════════════════════════════════════════════════════════════════════
def collect_wiktionary_xml(conn):
    print("\n[2] Tamil Wiktionary XML dump")
    url = "https://dumps.wikimedia.org/tawiktionary/latest/tawiktionary-latest-pages-articles.xml.bz2"
    data = download(url, "tawiktionary.xml.bz2", binary=True)
    if not data:
        print("  [SKIP]")
        return

    print("  Decompressing bz2...")
    try:
        xml_data = bz2.decompress(data)
    except Exception as e:
        print(f"  [ERROR] decompress: {e}")
        return

    rows = []
    in_page = False
    title = ""
    text_buf = []
    capturing = False

    print("  Parsing XML...")
    ns = "{http://www.mediawiki.org/xml/export-0.10/}"
    try:
        for event, elem in ET.iterparse(io.BytesIO(xml_data), events=("start","end")):
            tag = elem.tag.replace(ns, "")
            if event == "start" and tag == "page":
                title = ""
                text_buf = []
            elif event == "end" and tag == "title":
                title = (elem.text or "").strip()
            elif event == "end" and tag == "text":
                raw = elem.text or ""
                if is_tamil(title) and title:
                    # Extract meanings from wikitext
                    en_lines = re.findall(r'#\s*([^\n#\[{]+)', raw)
                    en_mean = "; ".join(l.strip() for l in en_lines[:5] if l.strip())
                    ta_lines = re.findall(r'\[\[([^\]|]+)\]\]', raw)
                    ta_mean = "; ".join(w for w in ta_lines[:5] if is_tamil(w))
                    rows.append((title, ta_mean or None, en_mean or None, None, "tawiktionary"))
                    if len(rows) >= 2000:
                        insert_batch(conn, rows)
                        rows = []
                elem.clear()
    except Exception as e:
        print(f"  [ERROR] parsing: {e}")
    insert_batch(conn, rows)
    print(f"  [DONE] Total DB: {count_words(conn):,}")

# ══════════════════════════════════════════════════════════════════════════
# SOURCE 3: PowerTamil / AgaraMuthali dictionary (GitHub)
# ══════════════════════════════════════════════════════════════════════════
def collect_powertamil(conn):
    print("\n[3] PowerTamil AgaraMuthali dictionary (~63k words)")
    # Raw JSON from GitHub
    urls = [
        ("https://raw.githubusercontent.com/rajkumarpal07/powertamil-dictionary/master/dict.json",
         "powertamil_dict.json"),
        ("https://raw.githubusercontent.com/rajkumarpal07/powertamil-dictionary/main/dict.json",
         "powertamil_dict_main.json"),
    ]
    data = None
    for url, cache in urls:
        data = download(url, cache)
        if data:
            break
    if not data:
        print("  [SKIP]")
        return

    try:
        entries = json.loads(data)
    except:
        print("  [ERROR] JSON parse failed")
        return

    rows = []
    if isinstance(entries, list):
        for e in entries:
            word = (e.get("word") or e.get("tamil") or "").strip()
            meaning = (e.get("meaning") or e.get("definition") or "").strip()
            if word and is_tamil(word):
                rows.append((word, meaning or None, None, None, "powertamil"))
    elif isinstance(entries, dict):
        for word, meaning in entries.items():
            if is_tamil(word):
                rows.append((word.strip(), str(meaning).strip() or None, None, None, "powertamil"))
    insert_batch(conn, rows)
    print(f"  [DONE] Total DB: {count_words(conn):,}")

# ══════════════════════════════════════════════════════════════════════════
# SOURCE 4: vigneshwaran-chandrasekaran/tamil-language-words-list
# ══════════════════════════════════════════════════════════════════════════
def collect_vignesh_wordlist(conn):
    print("\n[4] Tamil language words list (vigneshwaran)")
    urls = [
        "https://raw.githubusercontent.com/vigneshwaran-chandrasekaran/tamil-language-words-list/master/tamilwords.txt",
        "https://raw.githubusercontent.com/vigneshwaran-chandrasekaran/tamil-language-words-list/main/tamilwords.txt",
    ]
    data = None
    for url in urls:
        data = download(url, "vignesh_tamilwords.txt")
        if data:
            break
    if not data:
        print("  [SKIP]")
        return

    rows = []
    for line in data.splitlines():
        word = line.strip()
        if word and is_tamil(word):
            rows.append((word, None, None, None, "vignesh_wordlist"))
    insert_batch(conn, rows)
    print(f"  Added {len(rows):,} words | Total DB: {count_words(conn):,}")

# ══════════════════════════════════════════════════════════════════════════
# SOURCE 5: mskian Tamil words with English meaning (SQL/JSON)
# ══════════════════════════════════════════════════════════════════════════
def collect_mskian(conn):
    print("\n[5] mskian Tamil words with English meanings")
    urls_to_try = [
        ("https://raw.githubusercontent.com/mskian/Tamil-words-Collections-with-English-Meaning/master/words.json",
         "mskian_words.json"),
        ("https://raw.githubusercontent.com/mskian/Tamil-words-Collections-with-English-Meaning/main/words.json",
         "mskian_words_main.json"),
    ]
    data = None
    for url, cache in urls_to_try:
        data = download(url, cache)
        if data:
            break
    if not data:
        print("  [SKIP]")
        return
    try:
        entries = json.loads(data)
    except:
        print("  [ERROR]")
        return
    rows = []
    if isinstance(entries, list):
        for e in entries:
            word = (e.get("tamil") or e.get("word") or "").strip()
            en   = (e.get("english") or e.get("meaning") or "").strip()
            if word and is_tamil(word):
                rows.append((word, None, en or None, None, "mskian"))
    insert_batch(conn, rows)
    print(f"  [DONE] Total DB: {count_words(conn):,}")

# ══════════════════════════════════════════════════════════════════════════
# SOURCE 6: Open-Tamil (solthiruthi) word list
# ══════════════════════════════════════════════════════════════════════════
def collect_opentamil(conn):
    print("\n[6] Open-Tamil solthiruthi word list")
    word_files = [
        ("https://raw.githubusercontent.com/open-tamil/solthiruthi/master/data/tamilWords.txt",
         "opentamil_words.txt"),
        ("https://raw.githubusercontent.com/open-tamil/solthiruthi/master/data/tamilEnglish.txt",
         "opentamil_english.txt"),
    ]
    for url, cache in word_files:
        data = download(url, cache)
        if not data:
            continue
        rows = []
        for line in data.splitlines():
            parts = line.strip().split("\t")
            word = parts[0].strip() if parts else ""
            en   = parts[1].strip() if len(parts) > 1 else ""
            if word and is_tamil(word):
                rows.append((word, None, en or None, None, "opentamil"))
        insert_batch(conn, rows)
    print(f"  [DONE] Total DB: {count_words(conn):,}")

# ══════════════════════════════════════════════════════════════════════════
# SOURCE 7: Tamil Wikipedia dump — extract unique Tamil tokens
# ══════════════════════════════════════════════════════════════════════════
def collect_tamil_wikipedia(conn):
    print("\n[7] Tamil Wikipedia — extracting unique Tamil words")
    url = "https://dumps.wikimedia.org/tawiki/latest/tawiki-latest-all-titles-in-ns0.gz"
    data = download(url, "tawiki_titles.gz", binary=True)
    if not data:
        print("  [SKIP]")
        return
    try:
        text = gzip.decompress(data).decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  [ERROR] {e}")
        return

    tamil_word_re = re.compile(r'[\u0B80-\u0BFF][\u0B80-\u0BFF\u200C\u200D_]*')
    seen = set()
    rows = []
    for line in text.splitlines():
        title = line.strip().replace("_", " ")
        if is_tamil(title):
            # Add full title
            if title not in seen:
                seen.add(title)
                rows.append((title, None, None, None, "tawiki_title"))
            # Also extract individual Tamil words from title
            for w in tamil_word_re.findall(title):
                if len(w) > 1 and w not in seen:
                    seen.add(w)
                    rows.append((w, None, None, None, "tawiki_word"))
            if len(rows) >= 5000:
                insert_batch(conn, rows)
                rows = []
    insert_batch(conn, rows)
    print(f"  [DONE] Total DB: {count_words(conn):,}")

# ══════════════════════════════════════════════════════════════════════════
# SOURCE 8: Wiktionary-Dictionaries (Vuizur) Tamil-English TSV
# ══════════════════════════════════════════════════════════════════════════
def collect_vuizur_wiktionary(conn):
    print("\n[8] Vuizur Wiktionary Tamil-English TSV")
    url = "https://github.com/Vuizur/Wiktionary-Dictionaries/raw/main/dictionaries/Tamil-English.tsv"
    data = download(url, "vuizur_tamil_english.tsv")
    if not data:
        print("  [SKIP]")
        return
    rows = []
    for line in data.splitlines()[1:]:  # skip header
        parts = line.split("\t")
        if len(parts) >= 2:
            word = parts[0].strip()
            en   = parts[1].strip()
            if word and is_tamil(word):
                rows.append((word, None, en or None, None, "vuizur_wiktionary"))
    insert_batch(conn, rows)
    print(f"  [DONE] Total DB: {count_words(conn):,}")

# ══════════════════════════════════════════════════════════════════════════
# SOURCE 9: Tamil word frequency list (aviiciii)
# ══════════════════════════════════════════════════════════════════════════
def collect_word_frequency(conn):
    print("\n[9] Tamil word frequency list")
    url = "https://raw.githubusercontent.com/aviiciii/tamil-word-frequency/main/tamil_word_frequency.txt"
    data = download(url, "tamil_word_frequency.txt")
    if not data:
        url2 = "https://raw.githubusercontent.com/aviiciii/tamil-word-frequency/master/tamil_word_frequency.txt"
        data = download(url2, "tamil_word_frequency2.txt")
    if not data:
        print("  [SKIP]")
        return
    rows = []
    for line in data.splitlines():
        parts = line.strip().split()
        word = parts[0].strip() if parts else ""
        if word and is_tamil(word) and len(word) > 1:
            rows.append((word, None, None, None, "word_frequency"))
    insert_batch(conn, rows)
    print(f"  [DONE] Total DB: {count_words(conn):,}")

# ══════════════════════════════════════════════════════════════════════════
# SOURCE 10: IndicNLP Tamil stopwords + common words
# ══════════════════════════════════════════════════════════════════════════
def collect_indicnlp(conn):
    print("\n[10] IndicNLP Tamil resources")
    files = [
        ("https://raw.githubusercontent.com/AI4Bharat/IndicNLP/master/indicnlp/resources/stopwords/ta.txt",
         "ta_stopwords.txt"),
        ("https://raw.githubusercontent.com/AI4Bharat/IndicNLPSuite/master/indicnlp/resources/stopwords/ta.txt",
         "ta_stopwords2.txt"),
    ]
    for url, cache in files:
        data = download(url, cache)
        if not data:
            continue
        rows = []
        for line in data.splitlines():
            word = line.strip()
            if word and is_tamil(word):
                rows.append((word, None, None, None, "indicnlp"))
        insert_batch(conn, rows)
    print(f"  [DONE] Total DB: {count_words(conn):,}")

# ══════════════════════════════════════════════════════════════════════════
# EXPORT: Generate summary report
# ══════════════════════════════════════════════════════════════════════════
def generate_report(conn):
    print("\n" + "="*60)
    print("COLLECTION COMPLETE — SUMMARY")
    print("="*60)
    total = count_words(conn)
    print(f"Total unique word entries : {total:,}")

    rows = conn.execute("""
        SELECT source, COUNT(*) as cnt 
        FROM words GROUP BY source ORDER BY cnt DESC
    """).fetchall()
    print(f"\n{'Source':<25} {'Words':>10}")
    print("-"*37)
    for src, cnt in rows:
        print(f"{src:<25} {cnt:>10,}")

    with_en = conn.execute("SELECT COUNT(*) FROM words WHERE meaning_english IS NOT NULL AND meaning_english != ''").fetchone()[0]
    with_ta = conn.execute("SELECT COUNT(*) FROM words WHERE meaning_tamil IS NOT NULL AND meaning_tamil != ''").fetchone()[0]
    print(f"\nWords with English meaning : {with_en:,}")
    print(f"Words with Tamil meaning   : {with_ta:,}")
    print(f"\nDatabase saved to: {DB_PATH}")

    # Export a sample CSV
    csv_path = BASE_DIR / "tamil_dictionary_sample.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word","meaning_tamil","meaning_english","part_of_speech","source"])
        for row in conn.execute("SELECT word,meaning_tamil,meaning_english,part_of_speech,source FROM words LIMIT 5000"):
            writer.writerow(row)
    print(f"Sample CSV (5000 rows)     : {csv_path}")

    # Export full CSV
    full_csv = BASE_DIR / "tamil_dictionary_full.csv"
    print(f"\nExporting full CSV to      : {full_csv}")
    with open(full_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word","meaning_tamil","meaning_english","part_of_speech","source"])
        for row in conn.execute("SELECT word,meaning_tamil,meaning_english,part_of_speech,source FROM words"):
            writer.writerow(row)
    print("Full CSV export done!")

# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════
def main():
    print("="*60)
    print("TAMIL DICTIONARY COLLECTOR")
    print("="*60)

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    collectors = [
        collect_kaikki,
        collect_wiktionary_xml,
        collect_powertamil,
        collect_vignesh_wordlist,
        collect_mskian,
        collect_opentamil,
        collect_vuizur_wiktionary,
        collect_word_frequency,
        collect_indicnlp,
        collect_tamil_wikipedia,   # largest — run last
    ]

    for fn in collectors:
        try:
            fn(conn)
        except Exception as e:
            print(f"  [ERROR in {fn.__name__}]: {e}")

    generate_report(conn)
    conn.close()

if __name__ == "__main__":
    main()
