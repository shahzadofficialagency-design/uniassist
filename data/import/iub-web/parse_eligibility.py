"""Parse the official IUB eligibility-criteria page (saved HTML) into JSON.
Source: https://iub.edu.pk/index.php/eligibility-criteria (fetched 2026-11-16).
Table columns: Department | Program | Admission Criteria | Merit Formula,
grouped under faculty headings."""
import json, re
from html.parser import HTMLParser

SRC = "https://iub.edu.pk/index.php/eligibility-criteria"

class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.faculty = None
        self.in_table = 0
        self.row = None; self.cell = None; self.heading = None
        self.rows = []
    def handle_starttag(self, tag, attrs):
        if tag in ("h1","h2","h3","h4"): self.heading = ""
        if tag == "table": self.in_table += 1
        if self.in_table and tag == "tr": self.row = []
        if self.in_table and tag in ("td","th"): self.cell = ""
    def handle_endtag(self, tag):
        if tag in ("h1","h2","h3","h4") and self.heading is not None:
            h = re.sub(r"\s+", " ", self.heading).strip()
            if "facult" in h.lower() or "college" in h.lower(): self.faculty = h
            self.heading = None
        if tag == "table": self.in_table -= 1
        if self.in_table and tag in ("td","th") and self.cell is not None:
            self.row.append(re.sub(r"\s+", " ", self.cell).strip()); self.cell = None
        if self.in_table and tag == "tr" and self.row is not None:
            if len(self.row) == 4 and self.row[1] and "program" not in self.row[1].lower():
                self.rows.append({"faculty": self.faculty, "department": self.row[0],
                                  "program": self.row[1], "criteria": self.row[2],
                                  "merit_formula": self.row[3], "source_url": SRC})
            self.row = None
    def handle_data(self, d):
        if self.cell is not None: self.cell += d
        if self.heading is not None: self.heading += d

p = P()
p.feed(open("data/import/iub-web/iub_edu_pk_index_php_eligibility_criteria.html", encoding="utf-8", errors="ignore").read())
json.dump(p.rows, open("data/import/iub-web/eligibility.json", "w"), ensure_ascii=False, indent=1)
print("rows:", len(p.rows))
facs = {}
for r in p.rows: facs[r["faculty"]] = facs.get(r["faculty"], 0) + 1
for f, n in facs.items(): print(f"  {n:4d}  {f}")
for r in p.rows[:3]: print(r)
grad = [r for r in p.rows if any(k in r["program"] for k in ("MPhil","PhD","MS ","MSc"))]
print("graduate-level rows:", len(grad))
