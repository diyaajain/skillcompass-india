-- Job Market Skill Tracker: database schema (SQLite)

CREATE TABLE IF NOT EXISTS postings (
    id            TEXT PRIMARY KEY,      -- source's job id
    source        TEXT DEFAULT 'adzuna',
    title         TEXT,
    company       TEXT,
    location_raw  TEXT,
    city          TEXT,                  -- cleaned in the cleaning step
    salary_min    REAL,                  -- INR per year, when available
    salary_max    REAL,
    category      TEXT,
    contract_type TEXT,
    description   TEXT,
    posted_date   TEXT,                  -- ISO date
    url           TEXT,
    query         TEXT,                  -- search term that found it
    collected_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT UNIQUE NOT NULL,
    category   TEXT                      -- e.g. language, bi_tool, database
);

CREATE TABLE IF NOT EXISTS posting_skills (
    posting_id TEXT NOT NULL REFERENCES postings(id),
    skill_id   INTEGER NOT NULL REFERENCES skills(skill_id),
    PRIMARY KEY (posting_id, skill_id)
);

CREATE INDEX IF NOT EXISTS idx_postings_city ON postings(city);
CREATE INDEX IF NOT EXISTS idx_postings_date ON postings(posted_date);
CREATE INDEX IF NOT EXISTS idx_ps_skill ON posting_skills(skill_id);
