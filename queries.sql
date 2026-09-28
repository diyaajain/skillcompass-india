-- Analysis queries for the job market tracker (SQLite 3.25+ for window functions)
-- Run after: collect.py -> extract_skills.py -> clean.py
-- All queries exclude duplicates (is_dup = 0).

-- Q1. Which skills appear most often?
SELECT sk.skill_name,
       COUNT(*) AS postings,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM postings WHERE is_dup = 0), 1) AS pct_of_postings
FROM posting_skills ps
JOIN skills sk   ON sk.skill_id = ps.skill_id
JOIN postings p  ON p.id = ps.posting_id
WHERE p.is_dup = 0
GROUP BY sk.skill_name
ORDER BY postings DESC;

-- Q2. Median salary by skill (only skills with 30+ salaried postings)
WITH s AS (
    SELECT sk.skill_name, p.salary_mid,
           ROW_NUMBER() OVER (PARTITION BY sk.skill_name ORDER BY p.salary_mid) AS rn,
           COUNT(*)     OVER (PARTITION BY sk.skill_name) AS cnt
    FROM posting_skills ps
    JOIN skills sk  ON sk.skill_id = ps.skill_id
    JOIN postings p ON p.id = ps.posting_id
    WHERE p.is_dup = 0 AND p.salary_mid IS NOT NULL
)
SELECT skill_name, cnt AS salaried_postings, ROUND(AVG(salary_mid)) AS median_salary_inr
FROM s
WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)
GROUP BY skill_name, cnt
HAVING cnt >= 30
ORDER BY median_salary_inr DESC;

-- Q3. Skill pairs that co-occur most
SELECT a.skill_name AS skill_1, b.skill_name AS skill_2, COUNT(*) AS together
FROM posting_skills pa
JOIN posting_skills pb ON pa.posting_id = pb.posting_id AND pa.skill_id < pb.skill_id
JOIN skills a  ON a.skill_id = pa.skill_id
JOIN skills b  ON b.skill_id = pb.skill_id
JOIN postings p ON p.id = pa.posting_id
WHERE p.is_dup = 0
GROUP BY skill_1, skill_2
ORDER BY together DESC
LIMIT 20;

-- Q4. Skill demand by city (share of that city's postings), top cities only
WITH city_totals AS (
    SELECT city, COUNT(*) AS n FROM postings
    WHERE is_dup = 0 AND city NOT IN ('Other', 'Unspecified')
    GROUP BY city HAVING COUNT(*) >= 50
)
SELECT p.city, sk.skill_name,
       ROUND(100.0 * COUNT(*) / ct.n, 1) AS pct_of_city_postings
FROM posting_skills ps
JOIN postings p     ON p.id = ps.posting_id
JOIN skills sk      ON sk.skill_id = ps.skill_id
JOIN city_totals ct ON ct.city = p.city
WHERE p.is_dup = 0
GROUP BY p.city, sk.skill_name
ORDER BY p.city, pct_of_city_postings DESC;

-- Q5. Skill trend by week (needs a few weeks of daily collection to be meaningful)
WITH weekly AS (
    SELECT STRFTIME('%Y-%W', posted_date) AS week, COUNT(*) AS n
    FROM postings WHERE is_dup = 0 AND posted_date <> '' GROUP BY week
)
SELECT STRFTIME('%Y-%W', p.posted_date) AS week, sk.skill_name,
       ROUND(100.0 * COUNT(*) / w.n, 1) AS pct_of_week_postings
FROM posting_skills ps
JOIN postings p ON p.id = ps.posting_id
JOIN skills sk  ON sk.skill_id = ps.skill_id
JOIN weekly w   ON w.week = STRFTIME('%Y-%W', p.posted_date)
WHERE p.is_dup = 0 AND w.n >= 30
GROUP BY week, sk.skill_name
ORDER BY sk.skill_name, week;

-- Q6. Entry-level vs senior skill gap (share of postings requiring each skill)
WITH level_totals AS (
    SELECT seniority, COUNT(*) AS n FROM postings WHERE is_dup = 0 GROUP BY seniority
)
SELECT sk.skill_name,
       ROUND(100.0 * SUM(p.seniority = 'junior') / (SELECT n FROM level_totals WHERE seniority = 'junior'), 1) AS pct_junior,
       ROUND(100.0 * SUM(p.seniority = 'mid')    / (SELECT n FROM level_totals WHERE seniority = 'mid'), 1)    AS pct_mid,
       ROUND(100.0 * SUM(p.seniority = 'senior') / (SELECT n FROM level_totals WHERE seniority = 'senior'), 1) AS pct_senior
FROM posting_skills ps
JOIN postings p ON p.id = ps.posting_id
JOIN skills sk  ON sk.skill_id = ps.skill_id
WHERE p.is_dup = 0
GROUP BY sk.skill_name
ORDER BY pct_senior - pct_junior DESC;
