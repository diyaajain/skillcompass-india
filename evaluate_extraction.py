"""Compare extract_skills.py against your hand labels.

    python3 evaluate_extraction.py [labeled_csv]
Default: validation/to_label.csv. Prints per-skill precision/recall plus examples of
false positives (with context) so you can fix the regexes.
"""
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

from extract_skills import PATTERNS, SKILLS, find_skills

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("validation/to_label.csv")
df = pd.read_csv(path)

VALID = {name.lower(): name for name, cat, _ in SKILLS if cat != "soft_skill"}


def parse(cell):
    """Return a set of skills, or None if the row hasn't been labeled."""
    if pd.isna(cell) or not str(cell).strip():
        return None
    raw = str(cell).strip()
    if raw.upper() == "NONE":
        return set()
    out = set()
    for part in raw.split(";"):
        key = part.strip().lower()
        if not key:
            continue
        if key not in VALID:
            print(f"[warn] unknown skill name {part.strip()!r} (ignored)")
            continue
        out.add(VALID[key])
    return out


tp, fp, fn = defaultdict(int), defaultdict(int), defaultdict(int)
fp_examples, fn_examples = defaultdict(list), defaultdict(list)
labeled = 0

for _, row in df.iterrows():
    truth = parse(row["true_skills"])
    if truth is None:
        continue
    labeled += 1
    title = "" if pd.isna(row["title"]) else str(row["title"])
    desc = "" if pd.isna(row["description"]) else str(row["description"])
    text = f"{title} {desc}"
    pred = find_skills(text) & set(VALID.values())

    for s in pred & truth:
        tp[s] += 1
    for s in pred - truth:
        fp[s] += 1
        m = PATTERNS[s].search(text)
        ctx = text[max(0, m.start() - 40): m.end() + 40].replace("\n", " ")
        fp_examples[s].append(f"...{ctx}...")
    for s in truth - pred:
        fn[s] += 1
        fn_examples[s].append(title)

if labeled == 0:
    sys.exit("No labeled rows found. Fill in the 'true_skills' column first.")

rows = []
for s in VALID.values():
    support = tp[s] + fn[s]
    rows.append({
        "skill": s,
        "true_count": support,
        "tp": tp[s], "fp": fp[s], "fn": fn[s],
        "precision": round(tp[s] / (tp[s] + fp[s]), 2) if tp[s] + fp[s] else None,
        "recall": round(tp[s] / support, 2) if support else None,
    })
res = pd.DataFrame(rows).sort_values("true_count", ascending=False)
res.to_csv(path.with_suffix(".results.csv"), index=False)

T, F, N = sum(tp.values()), sum(fp.values()), sum(fn.values())
print(f"\nLabeled postings: {labeled}")
print(res.to_string(index=False))
print(f"\nOverall precision: {T / (T + F):.2f} | recall: {T / (T + N):.2f}" if T else "\nNo true positives yet.")
print("Skills with fewer than ~10 true mentions have unreliable percentages; report the counts.")

print("\n=== False positives (regex matched, you didn't label it) ===")
for s, ex in fp_examples.items():
    print(f"\n{s} ({len(ex)}):")
    for e in ex[:3]:
        print("  ", e)

print("\n=== Misses (you labeled it, regex didn't find it) ===")
for s, ex in fn_examples.items():
    print(f"\n{s} ({len(ex)}): e.g. {ex[:3]}")
    print("   -> search these postings for a synonym or spelling the regex lacks")
