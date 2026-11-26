"""Final matcher: official IUB eligibility rows -> fee-DB programs.
Rules (all deterministic, reported per match): degree normalisation
(B.Sc->BS, B.Ed/BS.Ed->BED), selective parenthesis handling (group/shift/
duration/acronym markers dropped, real name parts kept), stemming,
acronym keys (BEMS/BHMS), duration tiebreak, combined-row split,
dept-constrained aliases for official name variants."""
import json, re
from collections import defaultdict, Counter

def stem(tok):
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok

def base_prog(name):
    acro = re.search(r"\(([A-Z]{2,6})\)", name)
    protected = {t.lower() for t in re.findall(r"\b[A-Z]{3,6}\b", name)}
    s = " " + name.lower() + " "
    s = re.sub(r"\bb\.?\s*arch", " barch ", s)
    s = re.sub(r"\bb\.?\s?sc\.?\b", " bsc ", s)
    s = re.sub(r"\bm\.?\s?sc\.?\b", " msc ", s)
    s = re.sub(r"\bbs\.?\s?ed\.?\b", " bed ", s)
    s = re.sub(r"\bb\.?\s?ed\.?\b", " bed ", s)
    s = re.sub(r"\bbsc\b", " bs ", s); s = re.sub(r"\bmsc\b", " ms ", s)
    def _paren(m):
        c = m.group(1).strip()
        if any(k in c.lower() for k in ("group", "year", "sem", "after", "program", "duration")) \
           or c.lower() in ("evening", "morning", "mor", "eve", "e", "weekend") \
           or (len(c) <= 9 and re.fullmatch(r"[A-Z0-9][A-Za-z0-9.]{0,5}( [A-Z0-9]{1,5}){0,2}", c, re.I)):
            return " "
        return " " + c + " "
    s = re.sub(r"\(([^)]*)\)", _paren, s)
    s = s.replace(".", " ").replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    toks = []
    for t in s.split():
        if not t or t in ("group", "a", "b", "in", "hons", "honours", "years", "year",
                          "semesters", "semester", "program", "programme", "duration",
                          "morning", "evening", "weekend", "mor", "5th", "under", "system") \
           or t.isdigit():
            continue
        toks.append(t if t in protected else stem(t))
    merged, i = [], 0
    while i < len(toks):
        if toks[i] == "bio" and i + 1 < len(toks) and toks[i+1] in ("chemistry", "technology", "informatics"):
            merged.append("bio" + toks[i+1]); i += 2
        else:
            merged.append(toks[i]); i += 1
    out = " ".join(merged)
    if acro and out.split()[:1] == ["bachelor"]:
        return acro.group(1).lower()
    return out

def duration(name):
    m = re.search(r"(\d+(?:\.\d+)?)\s*-?\s*years", name.lower())
    return float(m.group(1)) if m else None

def dept_norm(s):
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^(department|dept|institute|school) of ", "", s)
    return " ".join(stem(t) for t in s.split())

def stemstr(x): return " ".join(stem(t) for t in x.split())

d = json.load(open("data/processed/programs.json"))
db = []
for f in d["faculties"]:
    for dep in f["departments"]:
        for p in dep["programs"]:
            db.append({"faculty": f["name"], "dept": dep["name"], "name": p["name"],
                       "dn": dept_norm(dep["name"]), "bn": base_prog(p["name"]),
                       "dur": duration(p["name"])})
for r in db: r["toks"] = set(r["bn"].split())

elig_raw = json.load(open("data/import/iub-web/eligibility.json"))
elig = []
for e in elig_raw:
    parts = [x.strip() for x in re.split(r"\s+/\s+", e["program"])]
    if len(parts) > 1 and all(re.match(r"(BS|BSc|B\.?Ed|LLB|Bachelor|M\.?Phil|PhD|Diploma)", x) for x in parts):
        for x in parts: elig.append({**e, "program": x, "split_from": e["program"]})
    else:
        elig.append(e)

by_key, by_base = defaultdict(list), defaultdict(list)
for i, r in enumerate(db):
    by_key[(r["dn"], r["bn"])].append(i); by_base[r["bn"]].append(i)

ALIASES = [(stemstr(a), stemstr(b), stemstr(c), stemstr(dd)) for a, b, c, dd in [
    ("english literature", "bs english literature", "english literature", "bs english language and literature"),
    ("architecture", "bachelor of architecture", "architecture", "barch"),
    ("translation studies", "bs translation studies", "translation studies", "bs translation and interpretation"),
    ("information security", "bs information and cyber security", "information security", "bs information security"),
    ("educational research and evaluation", "bed research and evaluation", "educational research and evaluation", "bed science"),
]]

results, unmatched = [], []
for e in elig:
    dn, bn, dur = dept_norm(e["department"]), base_prog(e["program"]), duration(e["program"])
    etoks = set(bn.split())
    hits, tier = [], None
    cand = by_key.get((dn, bn), [])
    if cand:
        if dur is not None:
            cd = [i for i in cand if db[i]["dur"] == dur]
            if cd: cand = cd
        hits, tier = cand, "exact_dept"
    if not hits:
        for wd, wb, dd, dbn in ALIASES:
            if wd in dn and bn == wb:
                cand = [i for i, r in enumerate(db) if dd in r["dn"] and (r["bn"] == dbn or r["bn"].startswith(dbn + " "))]
                if dur is not None:
                    cd = [i for i in cand if db[i]["dur"] == dur]
                    if cd: cand = cd
                if cand: hits, tier = cand, "alias"
                break
    if not hits:
        cand = by_base.get(bn, [])
        if cand:
            same_dept = [i for i in cand if db[i]["dn"] == dn]
            hits, tier = (same_dept or (cand if len({db[i]["dn"] for i in cand}) == 1 else []), "exact_base")
    if not hits:
        cand = [i for i, r in enumerate(db) if r["dn"] == dn and etoks and etoks <= r["toks"]]
        if cand: hits, tier = cand, "subset_dept"
    if not hits:
        cand = [i for i, r in enumerate(db) if etoks and etoks <= r["toks"]]
        if cand and len({db[i]["bn"] for i in cand}) == 1: hits, tier = cand, "subset_global"
    if not hits:
        best, score = [], 0.0
        for i, r in enumerate(db):
            j = len(etoks & r["toks"]) / max(1, len(etoks | r["toks"]))
            if j > score: best, score = [i], j
            elif j == score and j > 0: best.append(i)
        if score >= 0.8 and len({db[i]["bn"] for i in best}) == 1: hits, tier = best, f"fuzzy_{score:.2f}"
    if hits: results.append({"elig": e, "tier": tier, "db": [db[i] for i in hits]})
    else: unmatched.append(e)

covered = {r["name"] for res in results for r in res["db"]}
print(f"eligibility entries: {len(elig)}  matched: {len(results)}  unmatched: {len(unmatched)}")
print(f"DB programs covered: {len(covered)} / 457")
print(Counter(res["tier"].split("_")[0] for res in results))
print("\nSTILL UNMATCHED:")
for e in unmatched: print(f"  [{e['department']}] {e['program']}")
json.dump({"matches": [{"elig": r["elig"], "tier": r["tier"],
                        "db_names": [x["name"] for x in r["db"]],
                        "db_depts": [x["dept"] for x in r["db"]]} for r in results],
           "unmatched": unmatched},
          open("data/import/iub-web/match_final_result.json", "w"), ensure_ascii=False, indent=1)
