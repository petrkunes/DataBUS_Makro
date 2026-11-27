from pathlib import Path
import re

import pandas as pd

input_file = Path("data/Makro_CZSK_Export_whole_mod.csv")
output_dir = input_file.parent / "data-single"
column = "Vysledky_Objekt"

selected_values = {"Darko", "Profil_Stankovany_2B"}

# Read everything as text to preserve IDs, leading zeros, and empty cells.
df = pd.read_csv(
    input_file,
    sep=",",
    encoding="utf-8-sig",
    dtype=str,
    keep_default_na=False,
)

if column not in df.columns:
    raise ValueError(f"Column {column!r} not found in the CSV.")

# Select only the requested groups (exact, case-sensitive matches).
df = df.loc[df[column].isin(selected_values)].copy()

missing = selected_values - set(df[column])
if missing:
    raise ValueError(
        f"Requested values not found in {column!r}: "
        f"{', '.join(sorted(missing))}"
    )

output_dir.mkdir(parents=True, exist_ok=True)

# Prepare filenames and check for collisions before writing anything.
exports = []
used_names = {}

for value, group in df.groupby(column, sort=False):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value)
    name = name.strip().rstrip(".") or "_missing"

    filename = f"{name}.csv"

    # Also detect collisions on case-insensitive filesystems.
    key = filename.casefold()
    if key in used_names:
        raise ValueError(
            f"Filename collision: {value!r} and {used_names[key]!r} "
            f"would both produce {filename!r}."
        )

    used_names[key] = value
    exports.append((output_dir / filename, group))

# Check all output paths before writing any files.
for output_file, group in exports:
    if output_file.exists():
        raise FileExistsError(
            f"{output_file} already exists. "
            "Move or delete it before rerunning."
        )

# Write each group with the original column headers.
for output_file, group in exports:
    group.to_csv(
        output_file,
        sep=",",
        index=False,
        encoding="utf-8-sig",
    )
    print(f"{output_file.name}: {len(group):,} rows")

print(f"\nCreated {len(exports)} CSV files in {output_dir.resolve()}")