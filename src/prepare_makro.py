"""Add the columns DataBUS needs to data/CZ_makro_short.csv and write data/CZ_makro_long.csv.

Added columns:
  * `taxon`: `Vysledky_Taxon`, with the Czech names in TAXON_MAP translated,
  * `element`: the Czech element code (Vysledky_makrozbTyp) as a Neotoma element name,
  * `value` and `units`: the count (sumaCele) or weight (sumaHmot) of the row, with its unit,
  * `collector`, `datasetpi`, `sampleanalyst`: contacts as "Family, I." ("Roleček J., BÚ AVČR Brno"
    -> "Roleček, J.").

Run (from the repo root):
    uv run src/prepare_makro.py
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "CZ_makro_short.csv"
LONG = ROOT / "data" / "CZ_makro_long.csv"

# CONFIRM: the file does not state the units of sumaCele / sumaHmot; these are the working assumptions.
COUNT_UNIT = "NISP"
WEIGHT_UNIT = "grams"

# Raw role column -> new template column. CONFIRM: the file does not say which role each person has.
#   archVed (excavation lead) -> collector;  Botanik (botanist) -> dataset PI and sample analyst.
CONTACT_COLUMNS = {"collector": "archVed", "datasetpi": "Botanik", "sampleanalyst": "Botanik"}

ADDED_COLUMNS = ["taxon", "element", "value", "units"] + list(CONTACT_COLUMNS)

# Czech taxon names (Vysledky_Taxon) -> Neotoma ndb.taxa.taxonname. Every other name is used as written.
TAXON_MAP = {
    "uhlíky (ca 1mm)": "Charcoal",  # Czech for "charcoal (ca 1 mm)"
}

# Czech element code (Vysledky_makrozbTyp) -> Neotoma ndb.variableelements.variableelement.
# se/plod ("seed/fruit") -> "seed": that is the element Neotoma's existing plant-macrofossil variables
# Ask Petr to check translations.
ELEMENT_MAP = {
    "se/plod": "seed",
    "mech": "stem, leaf",
    "veget": "vegetative",
    "dřevo": "wood",
    "list": "leaf",
    "tobolka": "capsule",
    "periderm": "periderm",
    "šupina": "catkin scale",
    "spindl": "spindle",
    "uhlík": "charcoal",
}


def _number(text):
    """Return a float from a CSV cell, or None when it is blank."""
    text = text.strip()
    return round(float(text), 6) if text else None


def _text(value):
    """CSV text for a number: 50.0 -> "50", 0.25 -> "0.25"."""
    return str(int(value)) if float(value).is_integer() else str(value)


def format_contact(text):
    """Write contacts the way nh.get_contacts matches them: "Family, I." ("Roleček J., BÚ AVČR Brno").

    Returns "" for a cell that cannot be read (no initials found); the caller reports it. Several
    people separated by ";" are joined with "|", which DataBUS splits back into separate contacts.
    """
    people = []
    for person in text.split(";"):
        # Everything after the first comma is the affiliation ("BÚ AVČR Brno").
        words = person.split(",")[0].split()
        initials = []
        while words and len(words[-1]) == 2 and words[-1][0].isupper() and words[-1][1] == ".":
            initials.insert(0, words.pop())
        if not (words and initials):
            return ""
        people.append(f"{' '.join(words)}, {''.join(initials)}")
    return "|".join(people)


def read_raw():
    # utf-8-sig drops the BOM that the raw file starts with (the first header would otherwise be
    # "﻿Vyzkumy_Vyzkum").
    with open(RAW, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def add_columns(rows):
    """Return the rows with the added columns, and the contacts that could not be read."""
    unreadable = set()
    out_rows = []

    for row in rows:
        out = dict(row)
        # A row carries either a count (sumaCele) or a weight (sumaHmot), never both in this file.
        # A row with neither gets a blank value, which DataBUS skips.
        count, weight = _number(row["sumaCele"]), _number(row["sumaHmot"])
        if count is not None:
            value, units = count, COUNT_UNIT
        elif weight is not None:
            value, units = weight, WEIGHT_UNIT
        else:
            value, units = None, ""
        out["taxon"] = TAXON_MAP.get(row["Vysledky_Taxon"], row["Vysledky_Taxon"])
        code = row["Vysledky_makrozbTyp"]
        out["element"] = ELEMENT_MAP.get(code, code)
        out["value"] = "" if value is None else _text(value)
        out["units"] = units
        for column, raw_column in CONTACT_COLUMNS.items():
            out[column] = format_contact(row[raw_column])
            if row[raw_column].strip() and not out[column]:
                unreadable.add(row[raw_column])
        out_rows.append(out)
    return out_rows, unreadable


def main():
    raw_columns, rows = read_raw()
    out_rows, unreadable = add_columns(rows)
    with open(LONG, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(raw_columns) + ADDED_COLUMNS)
        writer.writeheader()
        writer.writerows(out_rows)
    samples = {r["Vzorky_Vzorek"] for r in out_rows}
    print(f"{len(rows)} rows, {len(samples)} samples; added {len(ADDED_COLUMNS)} columns")
    print(f"wrote {LONG.relative_to(ROOT)}")
    for text in sorted(unreadable):
        print(f"WARNING: could not read the contact {text!r}; left blank")


if __name__ == "__main__":
    main()
