import pytest

from clean import norm_city, role_family, salary_mid, seniority


@pytest.mark.parametrize("raw, expected", [
    ("Koramangala, Bengaluru, Karnataka", "Bengaluru"),
    ("Bangalore", "Bengaluru"),
    ("Gurgaon, Haryana", "Delhi NCR"),
    ("Noida, Uttar Pradesh", "Delhi NCR"),
    ("Navi Mumbai, Maharashtra", "Mumbai"),
    ("Ludhiana, Punjab", "Ludhiana"),
    ("Coimbatore, Tamil Nadu", "Coimbatore"),
    ("Trivandrum, Thiruvananthapuram", "Thiruvananthapuram"),
    ("India", "Unspecified"),
    ("Karnataka, India", "Unspecified"),
    ("Tamil Nadu, India", "Unspecified"),
    ("", "Unspecified"),
    (None, "Unspecified"),
    ("Ranchi, Jharkhand", "Other"),
    ("Barasat, North 24 Parganas", "Other"),
])
def test_norm_city(raw, expected):
    assert norm_city(raw) == expected


@pytest.mark.parametrize("title, expected", [
    ("Senior Data Analyst", "senior"),
    ("Sr. Business Analyst", "senior"),
    ("Lead Analyst", "senior"),
    ("Analytics Manager", "senior"),
    ("Junior Data Analyst", "junior"),
    ("Data Analyst Intern", "junior"),
    ("Data Analyst", "mid"),
    ("Internal Auditor", "mid"),   # "intern" must not match inside "internal"
    (None, "mid"),
])
def test_seniority(title, expected):
    assert seniority(title) == expected


@pytest.mark.parametrize("title, expected", [
    ("Data Analyst", "analyst"),
    ("Senior Business Analyst", "analyst"),
    ("Data Scientist", "data_science"),
    ("Machine Learning Engineer", "data_science"),
    ("Data Engineer", "data_engineering"),
    ("Tableau Developer", "bi"),
    ("Business Intelligence Specialist", "bi"),
    ("Project Manager", "other"),
    ("Assistant Manager", "other"),  # "ai" inside "assistant" must not trigger data_science
    (None, "other"),
])
def test_role_family(title, expected):
    assert role_family(title) == expected


@pytest.mark.parametrize("lo, hi, expected", [
    (500_000, 700_000, 600_000),
    (600_000, None, 600_000),
    (None, 800_000, 800_000),
    (None, None, None),
    (0, 0, None),
    (30_000, 40_000, None),               # looks monthly, below sanity range
    (50_000_000, 60_000_000, None),       # implausibly high
])
def test_salary_mid(lo, hi, expected):
    assert salary_mid(lo, hi) == expected
