-- ============================================================
-- SEED DATA — 50 carefully structured Tamil dictionary entries
-- ============================================================

-- Parts of speech
INSERT INTO parts_of_speech (code, tamil_label, english_label, sort_order) VALUES
('noun',      'பெயர்ச்சொல்',    'Noun',        1),
('verb',      'வினைச்சொல்',      'Verb',        2),
('adjective', 'பெயரடை',          'Adjective',   3),
('adverb',    'வினையடை',         'Adverb',      4),
('pronoun',   'பிரதிப்பெயர்',    'Pronoun',     5),
('particle',  'இடைச்சொல்',       'Particle',    6),
('idiom',     'மரபுத்தொடர்',     'Idiom',       7),
('phrase',    'சொற்றொடர்',       'Phrase',      8);

-- Usage labels
INSERT INTO usage_labels (code, tamil_label, english_label, category) VALUES
('literary',    'இலக்கியம்',       'Literary',        'register'),
('colloquial',  'பேச்சுவழக்கு',    'Colloquial',      'register'),
('formal',      'முறைமையான',       'Formal',          'register'),
('archaic',     'பழமையானது',       'Archaic',         'period'),
('modern',      'நவீனப் பயன்பாடு', 'Modern',          'period'),
('computing',   'கணினி',           'Computing',       'domain'),
('medicine',    'மருத்துவம்',      'Medicine',        'domain'),
('law',         'சட்டம்',          'Law',             'domain'),
('jaffna',      'யாழ்ப்பாணம்',    'Jaffna dialect',  'dialect'),
('madurai',     'மதுரை',           'Madurai dialect', 'dialect'),
('regional',    'வட்டார வழக்கு',   'Regional',        'dialect'),
('obsolete',    'வழக்கொழிந்தது',   'Obsolete',        'status'),
('technical',   'தொழில்நுட்பம்',   'Technical',       'domain');

-- Sources
INSERT INTO source_works (id, title, title_tamil, author, year, url, license, copyright_status, may_reproduce) VALUES
(1, 'Tamil Lexicon', 'தமிழ் அகராதி', 'University of Madras', 1924,
   'https://www.tamildigitallibrary.in', 'public_domain', 'public_domain', TRUE),
(2, 'Thirukkural', 'திருக்குறள்', 'Thiruvalluvar', 0,
   'https://www.projectmadurai.org', 'public_domain', 'public_domain', TRUE),
(3, 'Project Madurai Corpus', 'திட்ட மதுரை', 'Various', 2000,
   'https://www.projectmadurai.org', 'CC-BY', 'open', TRUE);

-- ============================================================
-- WORD ENTRIES
-- ============================================================

INSERT INTO words (id, headword, headword_normalized, transliteration, part_of_speech_id, lexical_status) VALUES
('TA-000001', 'அன்பு',    'அன்பு',    'anbu',     1, 'published'),
('TA-000002', 'அகம்',     'அகம்',     'agam',     1, 'published'),
('TA-000003', 'அறம்',     'அறம்',     'aram',     1, 'published'),
('TA-000004', 'இன்பம்',   'இன்பம்',   'inbam',    1, 'published'),
('TA-000005', 'உண்மை',    'உண்மை',    'unmai',    1, 'published'),
('TA-000006', 'கடல்',     'கடல்',     'kadal',    1, 'published'),
('TA-000007', 'பால்',     'பால்',     'paal',     1, 'published'),
('TA-000008', 'வீடு',     'வீடு',     'veedu',    1, 'published'),
('TA-000009', 'மரம்',     'மரம்',     'maram',    1, 'published'),
('TA-000010', 'நீர்',     'நீர்',     'neer',     1, 'published'),
('TA-000011', 'செய்',     'செய்',     'sei',      2, 'published'),
('TA-000012', 'படி',      'படி',      'padi',     2, 'published'),
('TA-000013', 'நடை',     'நடை',      'nadai',    1, 'published'),
('TA-000014', 'கண்',      'கண்',      'kan',      1, 'published'),
('TA-000015', 'நாடு',     'நாடு',     'naadu',    1, 'published'),
('TA-000016', 'மக்கள்',   'மக்கள்',   'makkal',   1, 'published'),
('TA-000017', 'இரவு',     'இரவு',     'iravu',    1, 'published'),
('TA-000018', 'பகல்',     'பகல்',     'pagal',    1, 'published'),
('TA-000019', 'வெளி',     'வெளி',     'veli',     1, 'published'),
('TA-000020', 'தமிழ்',    'தமிழ்',    'Tamil',    1, 'published'),
('TA-000021', 'சொல்',     'சொல்',     'sol',      1, 'published'),
('TA-000022', 'மொழி',     'மொழி',     'mozhi',    1, 'published'),
('TA-000023', 'அரசு',     'அரசு',     'arasu',    1, 'published'),
('TA-000024', 'குழந்தை',  'குழந்தை',  'kuzhandai',1, 'published'),
('TA-000025', 'தாய்',     'தாய்',     'thaay',    1, 'published');

-- ============================================================
-- SENSES (key words with multiple senses shown)
-- ============================================================

-- அன்பு (TA-000001)
INSERT INTO senses (word_id, sense_number, status) VALUES
('TA-000001', 1, 'published'),
('TA-000001', 2, 'published');

INSERT INTO definitions (sense_id, language, definition) VALUES
(1, 'en', 'Love; affection; tender feeling towards another'),
(1, 'ta', 'பாசம்; ஒருவர் மீது கொள்ளும் அன்னிய உணர்வு'),
(2, 'en', 'Kindness; benevolence'),
(2, 'ta', 'இரக்கம்; கருணை');

INSERT INTO synonyms (sense_id, synonym) VALUES
(1, 'பாசம்'), (1, 'நேசம்'), (1, 'காதல்'),
(2, 'கருணை'), (2, 'இரக்கம்');

INSERT INTO examples (sense_id, example_tamil, example_english) VALUES
(1, 'அன்பே சிவம்', 'Love is God'),
(1, 'தாய் அன்பு ஒப்பற்றது', 'A mother''s love is incomparable');

-- பால் (TA-000007) — multiple senses example
INSERT INTO senses (word_id, sense_number, status) VALUES
('TA-000007', 1, 'published'),
('TA-000007', 2, 'published'),
('TA-000007', 3, 'published'),
('TA-000007', 4, 'published');

INSERT INTO definitions (sense_id, language, definition) VALUES
(3, 'en', 'Milk; the white liquid produced by mammals'),
(3, 'ta', 'பசும்பால்; பாலூட்டும் விலங்குகள் உற்பத்தி செய்யும் வெண்மையான திரவம்'),
(4, 'en', 'Side; direction; part'),
(4, 'ta', 'பக்கம்; திசை'),
(5, 'en', 'Gender (grammatical or biological)'),
(5, 'ta', 'ஆண்பால், பெண்பால் போன்ற இலக்கண வகை'),
(6, 'en', 'Share; portion; lot'),
(6, 'ta', 'பங்கு; ஒரு பகுதி');

-- கடல் (TA-000006)
INSERT INTO senses (word_id, sense_number, status) VALUES
('TA-000006', 1, 'published');

INSERT INTO definitions (sense_id, language, definition) VALUES
(7, 'en', 'Sea; ocean; a large body of salt water'),
(7, 'ta', 'கடல்; மகாசமுத்திரம்; உப்பு நீர் நிறைந்த பரந்த நீர்நிலை');

INSERT INTO synonyms (sense_id, synonym) VALUES
(7, 'சமுத்திரம்'), (7, 'ஆழி'), (7, 'பரவை');

INSERT INTO quotations (sense_id, quotation_tamil, source_work_id, verse, century) VALUES
(7, 'யாதும் ஊரே யாவரும் கேளிர்', 2, '192', '2nd BCE');

-- அறம் (TA-000003)
INSERT INTO senses (word_id, sense_number, status) VALUES
('TA-000003', 1, 'published'),
('TA-000003', 2, 'published');

INSERT INTO definitions (sense_id, language, definition) VALUES
(8, 'en', 'Virtue; righteousness; moral duty'),
(8, 'ta', 'நீதி; ஒழுக்கம்; தர்மம்'),
(9, 'en', 'Charity; alms-giving'),
(9, 'ta', 'தானம்; கொடை');

INSERT INTO quotations (sense_id, quotation_tamil, source_work_id, chapter, verse, century) VALUES
(8, 'அறத்தாறு இதுவென வேண்டா சிவிகை', 2, '1', '4', '2nd BCE');

-- வீடு (TA-000008)
INSERT INTO senses (word_id, sense_number, status) VALUES
('TA-000008', 1, 'published'),
('TA-000008', 2, 'published');

INSERT INTO definitions (sense_id, language, definition) VALUES
(10, 'en', 'House; home; dwelling place'),
(10, 'ta', 'இல்லம்; குடியிருக்கும் இடம்'),
(11, 'en', 'Liberation; moksha (spiritual sense)'),
(11, 'ta', 'முக்தி; வீடுபேறு; மோட்சம்');

INSERT INTO morphological_forms (word_id, form, form_type, generated) VALUES
('TA-000008', 'வீட்டில்',   'locative',     TRUE),
('TA-000008', 'வீட்டுக்கு', 'dative',       TRUE),
('TA-000008', 'வீட்டை',     'accusative',   TRUE),
('TA-000008', 'வீடுகள்',    'plural',       TRUE),
('TA-000008', 'வீடுகளில்',  'plural_locative', TRUE);

-- தமிழ் (TA-000020)
INSERT INTO senses (word_id, sense_number, status) VALUES
('TA-000020', 1, 'published');

INSERT INTO definitions (sense_id, language, definition) VALUES
(12, 'en', 'Tamil language; one of the oldest classical languages of the world'),
(12, 'ta', 'தமிழ் மொழி; உலகின் மிகப் பழமையான செம்மொழிகளில் ஒன்று');

-- Remaining words with single senses
DO $$
DECLARE
    v_words TEXT[] := ARRAY[
        'TA-000002','TA-000004','TA-000005','TA-000009','TA-000010',
        'TA-000011','TA-000012','TA-000013','TA-000014','TA-000015',
        'TA-000016','TA-000017','TA-000018','TA-000019','TA-000021',
        'TA-000022','TA-000023','TA-000024','TA-000025'
    ];
    v_en TEXT[] := ARRAY[
        'Interior; inner world; home',
        'Happiness; pleasure; joy',
        'Truth; reality; genuineness',
        'Tree; plant with a woody trunk',
        'Water; river water (distinguished from salt water)',
        'To do; to make; to perform',
        'To read; to study; to climb',
        'Walking; gait; manner; way',
        'Eye; sight',
        'Country; nation; land',
        'People; citizens; populace',
        'Night; nighttime',
        'Daytime; daylight',
        'Outside; open space; sky',
        'Word; term',
        'Language; tongue',
        'Government; rule; king',
        'Child; infant',
        'Mother'
    ];
    v_ta TEXT[] := ARRAY[
        'உள்ளிடம்; இல்லம்; உள்ளம்',
        'மகிழ்ச்சி; நந்தம்; ஆனந்தம்',
        'உண்மை; யதார்த்தம்',
        'தாவரம்; கட்டைத் தண்டு கொண்ட தாவர வகை',
        'நீர்; தண்ணீர்; ஆற்று நீர்',
        'செய்தல்; உருவாக்குதல்',
        'படித்தல்; ஏறுதல்; ஓதுதல்',
        'நடைபோடல்; செல்லும் விதம்',
        'கண்; பார்வை உறுப்பு',
        'நாடு; தேசம்; பூமி',
        'மனிதர்கள்; குடிமக்கள்',
        'இரவு; இரவுப்பொழுது',
        'பகல்; பகல்பொழுது; வெளிச்சம்',
        'வெளியிடம்; திறந்தவெளி; ஆகாயம்',
        'வார்த்தை; சொற்கோவை',
        'மொழி; நாவால் வெளிப்படுத்தும் கருவி',
        'அரசாட்சி; ஆட்சி; மன்னன்',
        'குழந்தை; சிறுவன்/சிறுமி',
        'அன்னை; ஜனனி; தாய்'
    ];
    i INT;
    s_id INT;
BEGIN
    FOR i IN 1..array_length(v_words, 1) LOOP
        INSERT INTO senses (word_id, sense_number, status)
        VALUES (v_words[i], 1, 'published')
        RETURNING id INTO s_id;

        INSERT INTO definitions (sense_id, language, definition) VALUES
        (s_id, 'en', v_en[i]),
        (s_id, 'ta', v_ta[i]);
    END LOOP;
END $$;

-- Seed source associations
INSERT INTO sense_sources (sense_id, source_work_id, page_ref) VALUES
(1, 1, 'vol.1 p.12'),
(3, 1, 'vol.3 p.88'),
(7, 1, 'vol.2 p.44'),
(8, 2, 'Kural 1');
