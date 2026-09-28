# SkillCompass India

**What skills do Indian data analyst jobs ask for, and which should you learn first?**
An end-to-end analysis of [N] job postings: API data collection, SQL database, validated skill extraction, analysis, and an interactive dashboard.

**[Live dashboard →](https://skillcompass-india.streamlit.app/)**

![Dashboard screenshot](screenshots/dashboard-snippet.jpg)

## Key findings

> Replace the numbers below with your final results (re-run `analysis.py` after all fixes).

- **SQL appears in [X]% of analyst postings, [X]x as often as Python.** [X]% of postings that ask for Python also ask for SQL.
- **Power BI and Tableau** appear in [X]% and [X]% of postings. [One sentence on what this means, with the sampling caveat below.]
- **The most common skill pair is [SQL + Power BI]**, appearing together in [X] postings.
- **[City] leads with [X] postings**, followed by [City] and [City].
- **Salary:** the median advertised salary is ₹[X]L per year (based on [N] postings that state one). [One sentence on the skill comparison, if you have enough data.]
- **What to learn first:** [One-sentence recommendation based on your numbers, e.g. SQL first, then a BI tool, then Python.]

## Questions I set out to answer

1. Which skills are most in demand for analyst roles?
2. How do salaries differ for postings that mention different skills?
3. Which skills are typically asked for together?
4. How does demand differ across cities?
5. How do analyst requirements differ from data science requirements?

## Data and method

1. **Collection** (`collect.py`): pulled postings from the Adzuna API (India) for search terms such as "data analyst", "business analyst", "sql analyst", and "power bi". Retries with backoff handle API outages, and credentials are read from a git-ignored `.env` file.
2. **Storage** (`schema.sql`): SQLite database with three tables: `postings`, `skills`, `posting_skills`.
3. **Skill extraction** (`extract_skills.py`): regex matching for [N] skills across categories (languages, BI tools, databases, cloud, concepts).
4. **Cleaning** (`clean.py`): normalized city names, labeled seniority and role family from job titles, removed implausible salaries, and flagged [N] duplicate postings.
5. **Analysis** (`queries.sql`, `analysis.py`): SQL with joins, CTEs, and window functions for skill demand, co-occurrence, and median salary; pandas and matplotlib for charts.
6. **Dashboard** (`app.py`): Streamlit app with filters for role group, city, and seniority.
7. **Quality checks** (`tests/`, `evaluate_extraction.py`): unit tests for the cleaning and extraction logic, plus a hand-labeled validation of skill extraction (see below).

**Dataset:** [N] unique postings after removing duplicates, collected [dates]. [N] analyst/BI postings, [N] with a stated salary.

## Validation

Every finding depends on the skill extraction, so I measured it instead of assuming it works.

**Method.** I randomly sampled 100 analyst/BI postings and labeled which of the tracked skills each one actually mentions in its visible text, following written labeling rules (e.g. Excel counts for "pivot tables"; cloud platforms count only when named; nothing is inferred from the job title). The labels were drafted with Claude and spot-checked by me. I then compared them with the output of `extract_skills.py`.

**First pass (100 postings):**

| Skill | True mentions | Precision | Recall |
|---|---|---|---|
| SQL | 17 | 1.00 | 1.00 |
| Power BI | 16 | 1.00 | 0.94 |
| Tableau | 8 | 0.89 | 1.00 |
| Excel | 8 | 1.00 | 1.00 |
| Snowflake | 1 | 0.50 | 1.00 |
| **Overall (all skills)** | | **0.97** | **0.99** |

**Errors it found, and the fixes:**
- "Tableau CRM" (a separate Salesforce product) was counted as Tableau. Fixed with a negative lookahead.
- "star/snowflake schemas" (a data-modeling term) was counted as the Snowflake platform. Fixed.
- "Power Bl", a typo with a lowercase L, was missed. The pattern now tolerates it.
- Each fix has a regression test in `tests/test_extract.py`.

**After the fixes**, I re-measured on a fresh random sample of [50] postings that I had not tuned on: overall precision [X], recall [X].

**Reading these numbers honestly:**
- Skills with fewer than about 10 true mentions (all except SQL and Power BI here) have unreliable percentages, so I report their counts instead.
- Google Sheets, Pandas, AWS, NumPy, and VBA had no true mentions in the sample, so their accuracy is not evaluated.
- Labels use the same truncated text as the extractor, and AI-drafted labels follow the same keyword rules I wrote. Agreement is therefore likely higher than it would be for independent human labels, so I treat these figures as a sanity check plus a bug-finding tool, not a guarantee.

## Limitations

Being upfront about these matters more than hiding them.

- **This is a sample, not the whole market.** Results depend on my search terms and on what Adzuna indexes. Findings like "Power BI vs Tableau" describe this dataset.
- **Descriptions are truncated by the API** (about 500 characters), so skill counts are understated, especially skills mentioned late in a posting (e.g., Excel).
- **Skills are found by keyword matching**, which can miss synonyms and occasionally mismatch (see Validation).
- **Salary is missing for most postings** (about [X]% have one), so salary results are noisy and cover few skills.
- **Skill and salary are confounded.** Skills overlap heavily, so the salary chart shows postings that mention a skill, not what the skill is worth.
- **About [X]% of postings list only "India" or a state** and are excluded from city analysis.

## What went wrong (and what I did about it)

- The API returned 503 errors mid-collection. I added retries with exponential backoff and made inserts idempotent so re-runs never create duplicates.
- My first "Other" city bucket held 30% of the data. Investigating showed most were country-only locations, so I split it into "Unspecified" and "Other" instead of forcing a wrong city.
- Validating skill extraction on hand-labeled postings exposed false positives and a missed typo. I fixed them and added regression tests.
- API keys must never live in code. They are loaded from a git-ignored `.env` file, and error handling never prints the request URL, which contains the key.
- [Add your own: anything else that broke or surprised you.]

## Run it yourself

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt pytest
```

Create a file named `.env` in the project folder (it is git-ignored):

```
ADZUNA_APP_ID=your_id
ADZUNA_APP_KEY=your_key
```

Then run the pipeline in order:

```bash
python3 collect.py          # fetch postings into jobs.db
python3 extract_skills.py   # tag skills
python3 clean.py            # clean and flag duplicates (run before anything below)
pytest -q                   # unit tests
python3 analysis.py         # tables and charts in outputs/
python3 export_slim.py      # slim CSVs for the dashboard
streamlit run app.py
```

To reproduce the validation:

```bash
python3 make_validation_sample.py       # writes validation/to_label.csv
# fill the true_skills column, then:
python3 evaluate_extraction.py
```

## Project structure

```
├── collect.py                # API collection
├── extract_skills.py         # skill tagging (find_skills)
├── clean.py                  # cleaning and labeling
├── schema.sql                # database schema
├── queries.sql               # the analysis queries
├── analysis.py               # runs analysis, saves charts
├── export_slim.py            # exports dashboard data
├── app.py                    # Streamlit dashboard
├── make_validation_sample.py # samples postings for hand-labeling
├── evaluate_extraction.py    # precision/recall vs. hand labels
├── pytest.ini
├── requirements.txt
├── tests/
│   ├── test_clean.py
│   └── test_extract.py
├── data/                     # slim CSVs used by the dashboard
└── validation/               # labeled sample and results
```

`.env` and `jobs.db` are not committed.

## Next steps

- Collect daily (scheduled GitHub Action) to track how skill demand changes over time
- Improve skill extraction with a larger vocabulary or NLP
- Add a second data source to reduce single-API bias and truncated descriptions

## Tech

Python (pandas, requests, matplotlib, plotly), SQLite, Streamlit, pytest.

*Data from Adzuna. Built by Diya*
