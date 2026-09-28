"""Export a slim, shareable dataset for the dashboard (no descriptions or URLs).

    python3 export_slim.py
Writes data/postings.csv and data/posting_skills.csv. Re-run after each collect/clean.
"""
import sqlite3
from pathlib import Path

import pandas as pd

Path("data").mkdir(exist_ok=True)
conn = sqlite3.connect("jobs.db")

postings = pd.read_sql(
    """SELECT id, title, company, city, salary_mid, seniority, role_family, posted_date
       FROM postings WHERE is_dup = 0""",
    conn,
)
skills = pd.read_sql(
    """SELECT ps.posting_id, sk.skill_name, sk.category
       FROM posting_skills ps
       JOIN skills sk  ON sk.skill_id = ps.skill_id
       JOIN postings p ON p.id = ps.posting_id
       WHERE p.is_dup = 0""",
    conn,
)
postings.to_csv("data/postings.csv", index=False)
skills.to_csv("data/posting_skills.csv", index=False)
print(f"Exported {len(postings)} postings and {len(skills)} skill tags to data/")
