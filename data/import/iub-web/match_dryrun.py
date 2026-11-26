import json, re
from collections import defaultdict

def norm(s):
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def base_prog(name):
    s = name.lower()
    s = re.sub(r"\([^)]*\)", " ", s)                      # drop (Group-A), (Evening), (E)...
    s = s.replace("&", " and ")
    s = re.sub(r"\b(group|shift)\s*[ab]\b", " ", s)
    s = re.sub(r"\b(5th|morning|evening|weekend|mor)\b", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def dept_norm(s):
    s = norm(s)
    s = re.sub(r"^(department|dept|institute|school) of ", "", s)
    return s

d = json.load(open("data/processed/programs.json"))
db = []
for f in d["faculties"]:
    for dep in f["departments"]:
        for p in dep["programs"]:
            db.append({"faculty": f["name"], "dept": dep["name"], "name": p["name"],
                       "dn": dept_norm(dep["name"]), "bn": base_prog(p["name"])})

elig = json.load(open("data/import/iub-web/eligibility.json"))
by_db = defaultdict(list)   # db index -> elig row
by_key = defaultdict(list)
for i, r in enumerate(db): by_key[(r["dn"], r["bn"])].append(i)
by_base = defaultdict(list)
for i, r in enumerate(db): by_base[r["bn"]].append(i)

def toks(s): return set(s.split())
unmatched = []
matched_rows = 0
for e in elig:
    dn, bn = dept_norm(e["department"]), base_prog(e["program"])
    hits = by_key.get((dn, bn), [])
    if not hits and len(by_base.get(bn, [])) >= 1:
        cand = by_base[bn]
        hits = cand if len({db[i]["dn"] for i in cand}) == 1 or len(cand) <= 6 else []
    if not hits:  # fuzzy within same dept, then global
        best, score = [], 0.0
        for i, r in enumerate(db):
            if r["dn"] != dn: continue
            j = len(toks(bn) & toks(r["bn"])) / max(1, len(toks(bn) | toks(r["bn"])))
            if j > score: best, score = [i], j
            elif j == score and j > 0: best.append(i)
        if score >= 0.8: hits = best
    if hits:
        matched_rows += 1
        for i in hits: by_db[i].append(e)
    else:
        unmatched.append(e)

print(f"eligibility rows: {len(elig)}  matched: {matched_rows}  unmatched: {len(unmatched)}")
print(f"DB programs (of 457) getting a requirement: {len(by_db)}")
print("\nUNMATCHED eligibility rows:")
for e in unmatched: print(f"  [{e['department']}] {e['program']}")
json.dump({"covered": {str(i): v for i, v in by_db.items()},
           "db": db}, open("data/import/iub-web/match_result.json", "w"), ensure_ascii=False)
