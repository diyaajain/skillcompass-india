"""STEP 2: Tag each posting with skills found in its title + description.

Run after collect.py:
    python3 extract_skills.py
"""
import re
import sqlite3

DB_PATH = "jobs.db"

# (skill name, category, regex). Word boundaries avoid false hits like "sqlite" -> "sql".
SKILLS = [
    ("SQL", "database", r"\bsql\b|\bmysql\b|\bpostgres(ql)?\b|\bt-sql\b"),
    ("Python", "language", r"\bpython\b"),
    ("R", "language", r"\bR\b"),  # matched case-sensitively, see below
    ("Excel", "spreadsheet", r"\bexcel\b|\badvanced excel\b|\bvlookup\b|\bpivot tables?\b"),
    ("Power BI", "bi_tool", r"\bpower\s?bi\b"),
    ("Tableau", "bi_tool", r"\btableau\b"),
    ("Looker", "bi_tool", r"\blooker\b"),
    ("Google Sheets", "spreadsheet", r"\bgoogle sheets?\b"),
    ("Statistics", "concept", r"\bstatistic(s|al)?\b|\bhypothesis test(ing)?\b|\ba/b test(ing)?\b"),
    ("Machine Learning", "concept", r"\bmachine learning\b|\bscikit-learn\b|\bsklearn\b"),
    ("ETL", "concept", r"\betl\b|\bdata pipelines?\b"),
    ("Pandas", "library", r"\bpandas\b"),
    ("NumPy", "library", r"\bnumpy\b"),
    ("AWS", "cloud", r"\baws\b|\bamazon web services\b|\bredshift\b"),
    ("Azure", "cloud", r"\bazure\b"),
    ("GCP", "cloud", r"\bgcp\b|\bbigquery\b|\bgoogle cloud\b"),
    ("Snowflake", "cloud", r"\bsnowflake\b"),
    ("Spark", "big_data", r"\bspark\b|\bpyspark\b|\bhadoop\b"),
    ("SAS", "language", r"\bSAS\b"),  # case-sensitive
    ("VBA", "language", r"\bvba\b|\bmacros?\b"),
    ("Communication", "soft_skill", r"\bcommunication\b|\bstakeholders?\b|\bpresentation\b"),
]
CASE_SENSITIVE = {"R", "SAS"}


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # seed skills table and map name -> id
    for name, cat, _ in SKILLS:
        cur.execute("INSERT OR IGNORE INTO skills (skill_name, category) VALUES (?,?)", (name, cat))
    conn.commit()
    skill_ids = dict(cur.execute("SELECT skill_name, skill_id FROM skills"))

    compiled = [
        (name, re.compile(pat, 0 if name in CASE_SENSITIVE else re.IGNORECASE))
        for name, _, pat in SKILLS
    ]

    rows = cur.execute("SELECT id, COALESCE(title,''), COALESCE(description,'') FROM postings").fetchall()
    pairs = []
    for pid, title, desc in rows:
        text = f"{title} {desc}"
        for name, rx in compiled:
            if rx.search(text):
                pairs.append((pid, skill_ids[name]))

    cur.executemany("INSERT OR IGNORE INTO posting_skills (posting_id, skill_id) VALUES (?,?)", pairs)
    conn.commit()
    print(f"Processed {len(rows)} postings, {len(pairs)} skill tags.")
    conn.close()


if __name__ == "__main__":
    main()
