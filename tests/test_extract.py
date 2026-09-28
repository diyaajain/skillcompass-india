import pytest

from extract_skills import find_skills


def test_finds_multiple_skills():
    assert {"SQL", "Python"} <= find_skills("Experience with SQL and Python required")


@pytest.mark.parametrize("text", ["Power BI", "PowerBI dashboards", "experience in power bi"])
def test_power_bi_variants(text):
    assert "Power BI" in find_skills(text)


def test_sql_not_matched_inside_other_words():
    assert "SQL" not in find_skills("We use SQLite for prototypes")


def test_sql_matches_flavours():
    assert "SQL" in find_skills("Strong MySQL and PostgreSQL knowledge")


def test_r_language_matched():
    assert "R" in find_skills("Proficiency in R and Python")
    assert "R" in find_skills("Statistical tools (R/SAS)")


@pytest.mark.parametrize("text", ["Join our R&D team", "we are r&d focused", "Tier 1 support"])
def test_r_not_matched_in_unrelated_text(text):
    assert "R" not in find_skills(text)


def test_sas_is_case_sensitive():
    assert "SAS" in find_skills("Knowledge of SAS programming")
    assert "SAS" not in find_skills("a sas of a different kind")  # lowercase word


def test_empty_and_none():
    assert find_skills("") == set()
    assert find_skills(None) == set()
