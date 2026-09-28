"""STEP 3: Clean postings in jobs.db: normalize city, add seniority, clean salary, flag duplicates.

Run after collect.py and extract_skills.py:
    python3 clean.py
Safe to re-run.
"""
import re
import sqlite3

DB_PATH = "jobs.db"

# canonical city -> substrings to look for in the raw location (lowercase)
CITY_ALIASES = {
    "Bengaluru": ["bengaluru", "bangalore"],
    "Mumbai": ["mumbai", "navi mumbai", "thane", "bombay"],
    "Delhi NCR": ["delhi", "gurgaon", "gurugram", "noida", "ghaziabad", "faridabad"],
    "Hyderabad": ["hyderabad", "secunderabad"],
    "Pune": ["pune"],
    "Chennai": ["chennai"],
    "Kolkata": ["kolkata"],
    "Ahmedabad": ["ahmedabad"],
    "Jaipur": ["jaipur"],
    "Chandigarh": ["chandigarh", "mohali", "panchkula"],
    "Ludhiana": ["ludhiana"],
    "Kochi": ["kochi", "cochin", "ernakulam"],
    "Indore": ["indore"],
    "Coimbatore": ["coimbatore"],
    "Vadodara": ["vadodara", "baroda"],
    "Lucknow": ["lucknow"],
    "Surat": ["surat"],
    "Bhopal": ["bhopal"],
    "Nagpur": ["nagpur"],
    "Thiruvananthapuram": ["thiruvananthapuram", "trivandrum"],
}

SENIOR = r"\b(senior|sr\.?|lead|principal|manager|head|director|architect)\b"
JUNIOR = r"\b(junior|jr\.?|entry|fresher|associate|trainee|intern(ship)?|graduate)\b"

MIN_ANNUAL, MAX_ANNUAL = 100_000, 10_000_000  # INR/year sanity range


def norm_city(raw: str | None) -> str:
    text = (raw or "").lower().strip()
    for city, aliases in CITY_ALIASES.items():
        if any(a in text for a in aliases):
            return city
    parts = [p.strip() for p in text.split(",")]
    if not text or text == "india" or (len(parts) == 2 and parts[-1] == "india"):
        return "Unspecified"   # country or state only
    return "Other"

def role_family(title: str | None) -> str:
    t = (title or "").lower()
    if re.search(r"data scien|machine learning|\bml\b|\bai\b", t):
        return "data_science"
    if re.search(r"data engineer|\betl\b|big data", t):
        return "data_engineering"
    if re.search(r"analyst|analytics|reporting", t):
        return "analyst"
    if re.search(r"tableau|power\s?bi|business intelligence|\bbi\b", t):
        return "bi"
    return "other"


def seniority(title: str | None) -> str:
    t = (title or "").lower()
    if re.search(SENIOR, t):
        return "senior"
    if re.search(JUNIOR, t):
        return "junior"
    return "mid"


def salary_mid(lo, hi):
    vals = [v for v in (lo, hi) if v]
    if not vals:
        return None
    mid = sum(vals) / len(vals)
    return mid if MIN_ANNUAL <= mid <= MAX_ANNUAL else None


def add_column(cur, table, col, decl):
    try:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
    except sqlite3.OperationalError:
        pass  # already exists


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    add_column(cur, "postings", "seniority", "TEXT")
    add_column(cur, "postings", "salary_mid", "REAL")
    add_column(cur, "postings", "is_dup", "INTEGER DEFAULT 0")
    add_column(cur, "postings", "role_family", "TEXT")

    rows = cur.execute("SELECT id, title, location_raw, salary_min, salary_max FROM postings").fetchall()
    updates = [
        (norm_city(loc), seniority(title), salary_mid(lo, hi), role_family(title), pid)
        for pid, title, loc, lo, hi in rows
    ]
    cur.executemany(
        "UPDATE postings SET city=?, seniority=?, salary_mid=?, role_family=? WHERE id=?", updates
    )

    # same job found by several search terms / reposted: keep one copy
    cur.execute("UPDATE postings SET is_dup = 0")
    cur.execute(
        """UPDATE postings SET is_dup = 1 WHERE id NOT IN (
               SELECT MIN(id) FROM postings
               GROUP BY LOWER(title), LOWER(company), city, SUBSTR(description, 1, 200))"""
    )
    conn.commit()

    total, dups, with_sal = cur.execute(
        "SELECT COUNT(*), SUM(is_dup), COUNT(salary_mid) FROM postings"
    ).fetchone()
    print(f"{total} postings | {dups} duplicates flagged | {with_sal} with usable salary")
    print("Cities:", cur.execute(
        "SELECT city, COUNT(*) FROM postings WHERE is_dup=0 GROUP BY city ORDER BY 2 DESC"
    ).fetchall())
    conn.close()


if __name__ == "__main__":
    main()
