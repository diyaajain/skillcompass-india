"""STEP 4: Run the core analyses on analyst postings and save charts + CSVs to outputs/.

    python3 -m pip install pandas matplotlib
    python3 analysis.py

Change ROLE to 'data_science' to compare against data scientist postings.
"""
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DB = "jobs.db"
ROLE = "analyst/BI"
OUT = Path("outputs")
OUT.mkdir(exist_ok=True)

conn = sqlite3.connect(DB)
BASE = "p.is_dup = 0 AND p.role_family IN ('analyst', 'bi')"
FROM_SKILLS = """
    FROM posting_skills ps
    JOIN skills sk  ON sk.skill_id = ps.skill_id
    JOIN postings p ON p.id = ps.posting_id
"""


def barh(df, label_col, value_col, title, xlabel, path):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(df[label_col][::-1], df[value_col][::-1], color="#3b6ea5")
    ax.set_title(title, loc="left", fontweight="bold", fontsize=12)
    ax.set_xlabel(xlabel)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


n_total = pd.read_sql(f"SELECT COUNT(*) AS n FROM postings p WHERE {BASE}", conn).n[0]
print(f"Role: {ROLE} | postings: {n_total}")

# Q1. Most in-demand skills
q1 = pd.read_sql(f"SELECT sk.skill_name, COUNT(*) AS postings {FROM_SKILLS} WHERE {BASE} GROUP BY 1 ORDER BY 2 DESC", conn)
q1["pct_of_postings"] = (100 * q1.postings / n_total).round(1)
q1.to_csv(OUT / "q1_skill_demand.csv", index=False)
top = q1.head(10)
barh(top, "skill_name", "pct_of_postings",
     f"{top.skill_name[0]} appears in {top.pct_of_postings[0]}% of {ROLE} postings",
     "% of postings", OUT / "q1_skill_demand.png")
print("\nQ1 top skills:\n", top.to_string(index=False))

# Q2. Median salary by skill (INR/year, 30+ salaried postings)
sal = pd.read_sql(f"SELECT sk.skill_name, p.salary_mid {FROM_SKILLS} WHERE {BASE} AND p.salary_mid IS NOT NULL", conn)
overall = pd.read_sql(f"SELECT salary_mid FROM postings p WHERE {BASE} AND salary_mid IS NOT NULL", conn).salary_mid
print(f"\nQ2 salaried postings: {len(overall)} | overall median: {overall.median():,.0f}")
q2 = (sal.groupby("skill_name").salary_mid.agg(n="count", median_salary="median")
         .query("n >= 30").sort_values("median_salary", ascending=False).reset_index())
if q2.empty:
    print("Not enough salaried postings per skill (need 30+). Report this as a limitation.")
else:
    q2["median_salary_lakh"] = (q2.median_salary / 1e5).round(1)
    q2.to_csv(OUT / "q2_salary_by_skill.csv", index=False)
    barh(q2, "skill_name", "median_salary_lakh",
         f"{q2.skill_name[0]} postings pay the most (median ₹{q2.median_salary_lakh[0]}L/yr)",
         "Median salary (₹ lakh per year)", OUT / "q2_salary_by_skill.png")
    print(q2.to_string(index=False))

# Q3. Skills that appear together
q3 = pd.read_sql(f"""
    SELECT a.skill_name AS skill_1, b.skill_name AS skill_2, COUNT(*) AS together
    FROM posting_skills pa
    JOIN posting_skills pb ON pa.posting_id = pb.posting_id AND pa.skill_id < pb.skill_id
    JOIN skills a ON a.skill_id = pa.skill_id
    JOIN skills b ON b.skill_id = pb.skill_id
    JOIN postings p ON p.id = pa.posting_id
    WHERE {BASE}
    GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 15""", conn)
q3.to_csv(OUT / "q3_skill_pairs.csv", index=False)
print("\nQ3 top pairs:\n", q3.head(10).to_string(index=False))

# Q4. City breakdown (real cities only)
q4 = pd.read_sql(f"""
    SELECT city, COUNT(*) AS postings FROM postings p
    WHERE {BASE} AND city NOT IN ('Other', 'Unspecified')
    GROUP BY 1 ORDER BY 2 DESC""", conn)
q4.to_csv(OUT / "q4_postings_by_city.csv", index=False)
print("\nQ4 postings by city:\n", q4.head(8).to_string(index=False))

# Q6. Seniority mix
q6 = pd.read_sql(f"SELECT seniority, COUNT(*) AS postings FROM postings p WHERE {BASE} GROUP BY 1", conn)
print("\nQ6 seniority mix:\n", q6.to_string(index=False))

print(f"\nSaved CSVs and charts to {OUT}/")
conn.close()
