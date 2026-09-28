"""STEP 1: Collect job postings from the Adzuna API (India) into SQLite.

Setup:
    pip install requests python-dotenv
    Create a file named .env in this folder (never commit it) containing:
        ADZUNA_APP_ID=your_app_id
        ADZUNA_APP_KEY=your_app_key
Run:
    python3 collect.py
Safe to re-run: duplicates are ignored, so you can build up data daily.
"""
import os
import sqlite3
import time
from pathlib import Path

import requests

def load_env(filename: str = ".env") -> None:
    path = Path(__file__).with_name(filename)   # looks next to collect.py, wherever you run it from
    if not path.exists():
        print(f"[note] no {filename} file found next to collect.py")
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ[key.replace("export ", "").strip()] = value.strip().strip("'\"")


load_env()

DB_PATH = "jobs.db"
BASE_URL = "https://api.adzuna.com/v1/api/jobs/in/search/{page}"
QUERIES = ["data analyst", "business analyst", "sql analyst", "power bi", "junior data analyst",
           "tableau", "data scientist", "machine learning", "data engineer"]
PAGES_PER_QUERY = 10          # 50 results per page
RESULTS_PER_PAGE = 50


def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(Path("schema.sql").read_text())
    return conn


def get_credentials() -> tuple[str, str]:
    app_id = os.environ.get("ADZUNA_APP_ID", "").strip()
    app_key = os.environ.get("ADZUNA_APP_KEY", "").strip()
    if not app_id or not app_key:
        raise SystemExit(
            "ADZUNA_APP_ID / ADZUNA_APP_KEY are missing or empty. "
            "Put both in a .env file in this folder (see the docstring), then re-run."
        )
    return app_id, app_key


def fetch_page(query: str, page: int, credentials: tuple[str, str], retries: int = 5) -> list[dict]:
    app_id, app_key = credentials
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": RESULTS_PER_PAGE,
        "what": query,
        "content-type": "application/json",
    }
    for attempt in range(retries):
        try:
            resp = requests.get(BASE_URL.format(page=page), params=params, timeout=30)
        except requests.RequestException as e:
            problem = type(e).__name__          # never print the exception text: it contains the URL
        else:
            if resp.status_code == 200:
                return resp.json().get("results", [])
            if resp.status_code in (401, 403):
                raise SystemExit(f"HTTP {resp.status_code}: Adzuna rejected your credentials.")
            if resp.status_code != 429 and resp.status_code < 500:
                print(f"[skip] {query!r} page {page}: HTTP {resp.status_code} (not retryable)")
                return []
            problem = f"HTTP {resp.status_code}"
        wait = 2 ** attempt * 2
        print(f"[retry {attempt + 1}/{retries}] {query!r} page {page}: {problem} (waiting {wait}s)")
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
    credentials = get_credentials()   # stop immediately if keys are missing
    conn = init_db()
    total_new = 0
    for query in QUERIES:
        for page in range(1, PAGES_PER_QUERY + 1):
            jobs = fetch_page(query, page, credentials)
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