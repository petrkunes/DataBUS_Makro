"""Add the columns DataBUS needs to data/original/CZ_makro_short.csv and write data/CZ_makro_long.csv.

Added columns:
  * `taxon`: `Vysledky_Taxon`, with the Czech names in TAXON_MAP translated,
  * `element`: the Czech element code (Vysledky_makrozbTyp) as a Neotoma element name,
  * `value` and `units`: the count (sumaCele) or weight (sumaHmot) of the row, with its unit,
  * `collector`, `datasetpi`, `sampleanalyst`: contacts as "Family, I." ("Roleček J., BÚ AVČR Brno"
    -> "Roleček, J.").

Run (from the repo root):
    uv run src/prepare_makro.py
"""

import code
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "original" / "Makro_CZSK_Export_whole.csv"
LONG = ROOT / "data" / "Makro_CZSK_Export_whole_mod.csv"


# CONFIRM: the file does not state the units of sumaCele / sumaHmot; these are the working assumptions.
COUNT_UNIT = "NISP"
WEIGHT_UNIT = "grams"

# Raw role column -> new template column. CONFIRM: the file does not say which role each person has.
#   archVed (excavation lead) -> collector;  Botanik (botanist) -> dataset PI and sample analyst.
CONTACT_COLUMNS = {"collector": "archVed", "datasetpi": "Botanik", "sampleanalyst": "Botanik"}

ADDED_COLUMNS = ["country", "taxon", "element", "value", "units"] + list(CONTACT_COLUMNS)

# Country codes are changed to coutry names
COUNTRY_MAP = {
    "CZ": "Czech Republic",
    "SK": "Slovakia",
    "PL": "Poland",
}

# Czech taxon names (Vysledky_Taxon) -> Neotoma ndb.taxa.taxonname. Every other name is used as written.
TAXON_MAP = {
    "Abies/Picea": "Picea/Abies",
    "Acer cf.# campestre": "Acer cf. A. campestre",
    "Acer cf.# platanoides": "Acer cf. A. platanoides",
    "Acer spec.": "Acer sp.",
    "Achillea millefolium": "Achillea millefolium agg.",
    "Acinos": "Clinopodium",
    "Acinos arvensis": "Clinopodium acinos",
    "Agrostis spec.": "Agrostis sp.",
    "Ajuga genevensis/reptans": "Ajuga genevensis/A. reptans",
    "Alchemilla spec.#": "Alchemilla group",
    "Alchemilla vulgaris agg.": "Alchemilla sp.",
    "Alisma cf.# plantago-aquatica": "Alisma cf. A. plantago-aquatica",
    "Alnus cf.# glutinosa": "Alnus cf. A. glutinosa",
    "Alnus glutinosa/incana": "Alnus glutinosa/A. incana",
    "Alnus glutinosa/incana#": "Alnus glutinosa/A. incana",
    "Alnus sp./Betula sp.": "Betula/Alnus",
    "Alnus spec.#": "Alnus sp.",
    "Amaranthus#": "Amaranthus sp.",
    "Amblystegium kochii": "Hygroamblystegium humile",
    "Amblystegium sp.": "Amblystegium/Hygroamblystegium",
    "Anomodon attenuatus": "Pseudanomodon attenuatus",
    "Anthoxanthum odoratum agg.": "Anthoxanthum sp.",
    "Arctium minus s.l.": "Arctium cf. A. minus",
    "Artemisia spec.": "Artemisia sp.",
    "Atriplex nitens": "Atriplex sagittata",
    "Atriplex spec.#": "Atriplex sp.",
    "Barbula sp.= Didymodon tophaceus": "Didymodon tophaceus",
    "Batrachium sp.": "Ranunculus sect. Batrachium",
    "Batrachium species": "Ranunculus sect. Batrachium",
    "Betula cf.# pendula": "Betula cf. B. pendula",
    "Betula humilis/nana": "Betula humilis/B. nana",
    "Betula pendula/pubescens": "Betula pendula/B. pubescens",
    "Betula pendula/pubescens (alba-Typ)": "Betula pendula/B. pubescens",
    "Betula#": "Betula sp.",
    "Bidens tripartita ssp. bullata": "Bidens tripartita",
    "Brachythecium velutinum": "Brachytheciastrum velutinum",
    "Bromus spec.": "Bromus sp.",
    "Bryozooa": "Bryozoa",
    "Bryum pseudotriquetrum": "Ptychostomum pseudotriquetrum",
    "Calliergon sarmentosum": "Sarmentypnum sarmentosum",
    "Campanula spec.": "Campanula sp.",
    "Camptothecium lutescens": "Homalothecium lutescens",
    "Campylium elodes": "Campyliadelphus elodes",
    "Campylium polygamum": "Drepanocladus polygamus",
    "Sphagnum recurvum agg": "Sphagnum recurvum agg.",
    "Homalothecium nitens": "Tomentypnum nitens",
    "uhlíky (ca 1mm)": "Charcoal",  # Czech for "charcoal (ca 1 mm)"
    
}

# Czech element code (Vysledky_makrozbTyp) -> Neotoma ndb.variableelements.variableelement.
# se/plod ("seed/fruit") -> "seed": that is the element Neotoma's existing plant-macrofossil variables
# Ask Petr to check translations.
ELEMENT_MAP = {
    "bPluchy": "lemma base",
    "brachyblast": "short-shoot",
    "číška": "cupula",
    "diafragma": "diaphragm",
    "dř_kmen": "log",
    "dř_kořen": "root",
    "dř_větev": "branch",
    "dř_větv": "twig",
    "drevo": "wood",
    "epid": "epidermis",
    "f_sis": "megastrobilus",
    "f_šiš": "megastrobilus",
    "f-šiš": "megastrobilus",
    "houba": "hyphae",
    "jehlice": "needle",
    "jehněda": "catkin",
    "jiné": "unspecified",
    "jizva": "leaf scar",
    "klásek": "spikelet",
    "kolonie": "colony",
    "kořen": "root",
    "kosti": "bone",
    "kůra": "bark",
    "kvě_ství": "inflorescence",
    "květ": "flower",
    "listen": "bract",
    "m_šiš": "microstrobilus",
    "m_šiška": "microstrobilus",
    "megaspo": "megaspore",
    "mošnička": "perigynium",
    "nezn": "unspecified",
    "nod": "node",
    "obilka": "caryopsis",
    "odden": "rhizome",
    "oddenek": "rhizome",
    "oog": "oogonia",
    "oogonium": "oogonia",
    "oosp": "oospore",
    "oospora": "oospore",
    "oospores": "oospore",
    "oplodí": "pericarp",
    "oříšek": "nut",
    "peridermis": "periderm",
    "pletivo": "tissue",
    "pleva": "glume",
    "plo_ství": "infructescence",
    "plod": "fruit",
    "pupen": "bud",
    "řasa": "unspecified",
    "rhizom": "rhizome",
    "rostlina": "plant",
    "scarces": "leaf scar",
    "schránky": "test",
    "semeno": "seed",
    "šiška": "cone",
    "sklerocia": "sclerotium",
    "sklerocium": "sclerotium",
    "spindles": "spindle",
    "stéblo": "culm",
    "spor": "sporangium",
    "stat": "statoblast",
    "stéblo": "culm",
    "trn": "thorn",
    "tyč": "stamen",
    "uhlíky": "charcoal",
    "víčko": "operculum",
    "vřeteno": "spindle",
    "se/plod": "fruit/seed",
    "mech": "stem, leaf",
    "veget": "vegetative",
    "dřevo": "wood",
    "list": "leaf",
    "tobolka": "capsule",
    "periderm": "periderm",
    "šupina": "catkin scale",
    "spindl": "spindle",
    "uhlík": "charcoal",
    "křídlo": "wing",
    "větvička": "twig",
}

# Original element code -> (replacement taxon, replacement element).
# These overrides take precedence over TAXON_MAP and ELEMENT_MAP.
ELEMENT_TAXON_OVERRIDES = {
    "ršup": ("Osteichthyes undiff.", "scale"),
    "rzub": ("Osteichthyes undiff.", "tooth"),
    "ryby": ("Osteichthyes undiff.", "tooth"),
    "ostr": ("Ostracoda", "unspecified"),
    "měkk": ("Mollusca", "valve"),
    "hmyz": ("Insecta indet.", "unspecified"),
    "clad": ("Cladocera undiff.", "unspecified"),
    "Clad": ("Cladocera undiff.", "unspecified"),

    # Add further rules using the same structure:
    # "original_code": ("replacement taxon", "replacement element"),
}


def _number(text):
    """Return a float from a CSV cell, or None when it is blank."""
    text = text.strip()
    return round(float(text), 6) if text else None


def _text(value):
    """CSV text for a number: 50.0 -> "50", 0.25 -> "0.25"."""
    return str(int(value)) if float(value).is_integer() else str(value)

CONTACT_MAP = {
    "Chaloupková": "Chaloupková, K.",
    "Dohnal, Mejstřík": "Dohnal, Z.|Mejstřík, V.",
    "Hájková, Ústav botaniky a zoologie PřF MU, Brno": "Hájková, P.",
    "Jankovská": "Jankovská, V.",
    "Novák Jan": "Novák, J.",
    "Petr Pokorný, CTS": "Pokorný, P.",
    "Petra Hájková, Ústav botaniky a zoologie PřF MU, Brno": "Hájková, P.",
    "Novák Jan, PřF UK Praha": "Novák, J.",
    "Petřík Jan, Masarykova univerzita, Brno": "Petřík, J.",
    "Pišút Peter, Katedra fyzickej geografie a geoinformatiky, Univerzita Komenského v Bratislavě": "Pišút, P.",
    "Péter Tóth": "Tóth, P.",
    "Stachowicz-Rybka Renata, W. Szafer Institute of Botany, Polish Academy of Sciences": "Stachowicz-Rybka, R.",
    "Treml V. PrF UK": "Treml, V.",
    "Šolcová A. (Potůčková)": "Šolcová, A.",
    "Šolcová A. (Potůčková), Katedra botaniky, PřF UK, Praha": "Šolcová, A.",
}

def format_contact(text):
    """Resolve manual overrides first, then format contacts automatically."""
    """Write contacts the way nh.get_contacts matches them: "Family, I." ("Roleček J., BÚ AVČR Brno").

     Returns "" for a cell that cannot be read (no initials found); the caller reports it. Several
     people separated by ";" are joined with "|", which DataBUS splits back into separate contacts.
     """
    text = (text or "").strip()

    if not text:
        return ""

    # Override the entire cell, including unusual multi-person entries.
    if text in CONTACT_MAP:
        return CONTACT_MAP[text]

    people = []

    for person in text.split(";"):
        person = person.strip()

        if not person:
            continue

        # Override an individual person within a multi-person cell.
        if person in CONTACT_MAP:
            mapped = CONTACT_MAP[person]

            if not mapped:
                return ""

            people.append(mapped)
            continue

        # Automatic fallback: remove affiliation and extract initials.
        words = person.split(",")[0].split()
        initials = []

        while (
            words
            and len(words[-1]) == 2
            and words[-1][0].isupper()
            and words[-1][1] == "."
        ):
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
        
        raw_taxon = row["Vysledky_Taxon"]
        code = row["Vysledky_makrozbTyp"].strip()
        
        out["taxon"] = TAXON_MAP.get(raw_taxon, raw_taxon)
        # code = row["Vysledky_makrozbTyp"]
        out["element"] = ELEMENT_MAP.get(code, code)

        # Override both values when the original element code has a special rule.
        if code in ELEMENT_TAXON_OVERRIDES:
            out["taxon"], out["element"] = ELEMENT_TAXON_OVERRIDES[code]
        
        out["country"] = COUNTRY_MAP.get(row["Stat"], row["Stat"])
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
