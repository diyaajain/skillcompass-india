"""STEP 1: Collect job postings from the Adzuna API (India) into SQLite.

Setup:
    pip install requests
    export ADZUNA_APP_ID= 045df08e   (Windows: set ADZUNA_APP_ID=...)
    export ADZUNA_APP_KEY= a29f4b6f77f7fde98b91a7bd3f0e24e8   (Windows: set ADZUNA_APP_KEY=...)
Run:
    python3 collect.py
Safe to re-run: duplicates are ignored, so you can build up data daily.
"""
import os
import sqlite3
import time
from pathlib import Path

import requests

DB_PATH = "jobs.db"
BASE_URL = "https://api.adzuna.com/v1/api/jobs/in/search/{page}"
QUERIES = ["data analyst", "business analyst", "sql analyst", "power bi", "junior data analyst", "tableau", "data scientist", "machine learning", "data engineer"]
PAGES_PER_QUERY = 10          # 50 results per page
RESULTS_PER_PAGE = 50


def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(Path("schema.sql").read_text())
    return conn


def fetch_page(query: str, page: int, retries: int = 5) -> list[dict]:
    params = {
        "app_id": os.environ["ADZUNA_APP_ID"],
        "app_key": os.environ["ADZUNA_APP_KEY"],
        "results_per_page": RESULTS_PER_PAGE,
        "what": query,
        "content-type": "application/json",
    }
    for attempt in range(retries):
        try:
            resp = requests.get(BASE_URL.format(page=page), params=params, timeout=30)
            if resp.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"HTTP {resp.status_code}")
            resp.raise_for_status()
            return resp.json().get("results", [])
        except requests.RequestException as e:
            wait = 2 ** attempt * 2  # 2s, 4s, 8s, 16s, 32s
            print(f"[retry {attempt + 1}/{retries}] {query!r} page {page}: {e} (waiting {wait}s)")
            time.sleep(wait)
    print(f"[gave up] {query!r} page {page}")
    return []


def to_row(job: dict, query: str) -> tuple:
    return (
        str(job["id"]),
        job.get("title"),
        (job.get("company") or {}).get("display_name"),
        (job.get("location") or {}).get("display_name"),
        job.get("salary_min"),
        job.get("salary_max"),
        (job.get("category") or {}).get("label"),
        job.get("contract_type"),
        job.get("description"),
        (job.get("created") or "")[:10],
        job.get("redirect_url"),
        query,
    )


def main() -> None:
    conn = init_db()
    total_new = 0
    for query in QUERIES:
        for page in range(1, PAGES_PER_QUERY + 1):
            try:
                jobs = fetch_page(query, page)
            except requests.RequestException as e:
                print(f"[warn] {query!r} page {page}: {e}")
                break
            if not jobs:
                break
            before = conn.total_changes
            conn.executemany(
                """INSERT OR IGNORE INTO postings
                   (id, title, company, location_raw, salary_min, salary_max,
                    category, contract_type, description, posted_date, url, query)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                [to_row(j, query) for j in jobs],
            )
            conn.commit()
            total_new += conn.total_changes - before
            print(f"{query!r} page {page}: {len(jobs)} fetched")
            time.sleep(2)  # be polite to the API
    print(f"Done. {total_new} new postings added.")
    conn.close()


if __name__ == "__main__":
    main()
