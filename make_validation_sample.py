"""Sample postings for hand-labeling.

    python3 make_validation_sample.py [seed] [n] [out_csv]
Defaults: seed 42, n 100, validation/to_label.csv
Use a different seed and path for a fresh test set after you fix regexes.
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

from extract_skills import SKILLS

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
n = int(sys.argv[2]) if len(sys.argv) > 2 else 100
out = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("validation/to_label.csv")
out.parent.mkdir(exist_ok=True)

conn = sqlite3.connect("jobs.db")
df = pd.read_sql(
    """SELECT id AS posting_id, title, description FROM postings
       WHERE is_dup = 0 AND role_family IN ('analyst', 'bi')""",
    conn,
)
sample = df.sample(n=min(n, len(df)), random_state=seed).copy()
sample["true_skills"] = ""
sample.to_csv(out, index=False)

names = [name for name, cat, _ in SKILLS if cat != "soft_skill"]
print(f"Wrote {len(sample)} postings to {out}")
print("\nFill the 'true_skills' column using ONLY these names, separated by ';':")
print("  " + "; ".join(names))
print("Write NONE if a posting mentions none of them. Don't look at extractor output first.")
