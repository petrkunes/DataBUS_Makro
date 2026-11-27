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

LONG = "data/Makro_CZSK_Export_whole_mod.csv"
OUT = "data/validation_logs/CZ_makro_missing_variables.csv"

QUERY = """
SELECT
    ARRAY(
        SELECT taxonid
        FROM ndb.taxa
        WHERE LOWER(taxonname) = LOWER(%(taxon)s)
        ORDER BY taxonid
    ),
    ARRAY(
        SELECT variableelementid
        FROM ndb.variableelements
        WHERE LOWER(variableelement) = LOWER(%(element)s)
        ORDER BY variableelementid
    ),
    ARRAY(
        SELECT variableunitsid
        FROM ndb.variableunits
        WHERE LOWER(variableunits) = LOWER(%(unit)s)
        ORDER BY variableunitsid
    )
"""

EXISTS = """
SELECT 1 FROM ndb.variables
WHERE taxonid = %s AND variableelementid = %s AND variableunitsid = %s
  AND variablecontextid IS NULL
"""


def main():
    load_dotenv()
    raw = os.getenv("PGDB_LOCAL")
    if raw is None:
        raise SystemExit("PGDB_LOCAL is not set. Add it to .env (JSON passed to psycopg2.connect).")
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
    n_valid = 0
    n_ambiguous = 0

    for (taxon, element, unit), (n_rows, samples) in sorted(found.items()):
        cur.execute(
            QUERY,
            {"taxon": taxon, "element": element, "unit": unit},
        )

        taxon_ids, element_ids, unit_ids = cur.fetchone()

        lookups = [
            ("taxon", taxon_ids),
            ("element", element_ids),
            ("units", unit_ids),
        ]

        parts = []
        ambiguous = False

        for name, ids in lookups:
            if not ids:
                parts.append(name)
            elif len(ids) > 1:
                parts.append(f"ambiguous_{name}")
                ambiguous = True
                print(
                    f"WARNING: ambiguous {name} for "
                    f"{(taxon, element, unit)!r}: IDs {ids}"
                )

        # Check the variable only when all three lookups are unique.
        if not parts:
            cur.execute(
                EXISTS,
                (taxon_ids[0], element_ids[0], unit_ids[0]),
            )

            if cur.fetchone() is None:
                parts.append("variable")

        if ambiguous:
            n_ambiguous += 1

        if parts:
            missing.append(
                (
                    taxon,
                    element,
                    unit,
                    "+".join(parts),
                    n_rows,
                    ",".join(sorted(samples)),
                )
            )
        else:
            n_valid += 1

    conn.close()

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["taxon", "element", "units", "missing", "n_rows", "samples"])
        writer.writerows(missing)
    print(
    f"{n_valid} of {len(found)} combinations confirmed; "
    f"{len(missing)} unresolved "
    f"(including {n_ambiguous} ambiguous) -> {OUT}"
)
    for reason in sorted({m[3] for m in missing}):
        group = [m for m in missing if m[3] == reason]
        print(f"  missing {reason}: {len(group)} combinations, {sum(m[4] for m in group)} rows")


if __name__ == "__main__":
    main()
