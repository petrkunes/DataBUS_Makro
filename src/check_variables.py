"""List what is still missing in Neotoma for the long file: taxa, elements, units and variables.

DataBUS does not create rows in ndb.taxa, ndb.variableelements, ndb.variableunits or ndb.variables:
valid_data looks a variable up by (taxonid, variableelementid, variableunitsid) and logs a FALSE for
every name or combination it cannot find. That log does not say how many rows or samples a gap
affects, so this helper (read-only) lists each distinct taxon x element x units of the file.

Run (from the repo root, after `uv run src/prepare_makro.py`):
    uv run src/check_variables.py
Writes data/validation_logs/CZ_makro_missing_variables.csv: one row per missing combination, `missing` says which part
(taxon, element, units, or variable = all three exist but not together), plus the number of data rows
and the samples affected.
"""

import csv
import json
import os

import psycopg2
from dotenv import load_dotenv

LONG = "data/CZ_makro_long.csv"
OUT = "data/validation_logs/CZ_makro_missing_variables.csv"

QUERY = """
SELECT (SELECT taxonid FROM ndb.taxa WHERE LOWER(taxonname) = LOWER(%(taxon)s)),
       (SELECT variableelementid FROM ndb.variableelements
         WHERE LOWER(variableelement) = LOWER(%(element)s)),
       (SELECT variableunitsid FROM ndb.variableunits
         WHERE LOWER(variableunits) = LOWER(%(unit)s))
"""
EXISTS = """
SELECT 1 FROM ndb.variables
WHERE taxonid = %s AND variableelementid = %s AND variableunitsid = %s
  AND variablecontextid IS NULL
"""


def main():
    load_dotenv()
    raw = os.getenv("PGDB_TANK")
    if raw is None:
        raise SystemExit("PGDB_TANK is not set. Add it to .env (JSON passed to psycopg2.connect).")
    conn = psycopg2.connect(**json.loads(raw), connect_timeout=5)
    conn.set_session(readonly=True)  # this helper never writes
    cur = conn.cursor()

    # The variables are the distinct taxon (Vysledky_Taxon) / element / units triples of the file.
    with open(LONG, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    found = {}
    for r in rows:
        entry = found.setdefault((r["taxon"], r["element"], r["units"]), [0, set()])
        entry[0] += 1
        entry[1].add(r["Vzorky_Vzorek"])

    missing = []
    for (taxon, element, unit), (n_rows, samples) in sorted(found.items()):
        cur.execute(QUERY, {"taxon": taxon, "element": element, "unit": unit})
        taxonid, elementid, unitid = cur.fetchone()
        parts = [
            name
            for name, found_id in (("taxon", taxonid), ("element", elementid), ("units", unitid))
            if found_id is None
        ]
        if not parts:
            cur.execute(EXISTS, (taxonid, elementid, unitid))
            if not cur.fetchone():
                parts = ["variable"]
        if parts:
            missing.append(
                (taxon, element, unit, "+".join(parts), n_rows, ",".join(sorted(samples)))
            )
    conn.close()

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["taxon", "element", "units", "missing", "n_rows", "samples"])
        writer.writerows(missing)
    print(
        f"{len(found) - len(missing)} of {len(found)} taxon/element/units combinations exist; "
        f"{len(missing)} missing -> {OUT}"
    )
    for reason in sorted({m[3] for m in missing}):
        group = [m for m in missing if m[3] == reason]
        print(f"  missing {reason}: {len(group)} combinations, {sum(m[4] for m in group)} rows")


if __name__ == "__main__":
    main()
