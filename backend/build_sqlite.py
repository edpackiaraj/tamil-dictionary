import gzip
import csv
import sqlite3
import os
import uuid

def build_db():
    csv_path = "data/tamil_dictionary_full.csv.gz"
    db_path = "data/tamil_dictionary.db"
    
    if os.path.exists(db_path):
        print(f"{db_path} already exists, skipping build.")
        return
        
    print(f"Building {db_path} from {csv_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT,
            meaning_tamil TEXT,
            meaning_english TEXT,
            part_of_speech TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_word ON words(word)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_english ON words(meaning_english)")
    
    batch = []
    count = 0
    with gzip.open(csv_path, "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            batch.append((
                row.get("word", ""),
                row.get("meaning_tamil", ""),
                row.get("meaning_english", ""),
                row.get("part_of_speech", ""),
                row.get("source", "")
            ))
            count += 1
            if len(batch) >= 10000:
                cursor.executemany("""
                    INSERT INTO words (word, meaning_tamil, meaning_english, part_of_speech, source)
                    VALUES (?, ?, ?, ?, ?)
                """, batch)
                batch = []
                
        if batch:
            cursor.executemany("""
                INSERT INTO words (word, meaning_tamil, meaning_english, part_of_speech, source)
                VALUES (?, ?, ?, ?, ?)
            """, batch)
            
    conn.commit()
    conn.close()
    print(f"Successfully built SQLite DB with {count} words!")

if __name__ == "__main__":
    build_db()
