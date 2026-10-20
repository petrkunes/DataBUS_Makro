"""Validate (and optionally upload) the Czech macrofossil file with DataBUS.

Two-pass workflow (run from the repo root):
    uv run src/prepare_makro.py
    uv run src/template_validate.py --template src/templates/template.yml
    uv run src/template_validate.py --template src/templates/template.yml --upload true

Every csv/xlsx file in data/ is read. The log goes to data/validation_logs/<file>.valid.log, or to
data/upload_logs/<file>.upload.log with --upload true, which only commits if the last validation of
that exact file was clean. Without --upload the transaction is always rolled back.
The database comes from PGDB_TANK in .env. Steps for chronologies and geochronologies are not part
of this dataset; see DataBUS/validation_playground.py to add them.
"""

import glob
import json
import os
from datetime import datetime

import DataBUS.neotomaHelpers as nh
import DataBUS.neotomaValidator as nv
import psycopg2
from dotenv import load_dotenv

args = nh.parse_arguments()
load_dotenv()
connection = json.loads(os.getenv("PGDB_TANK"))

validation_dir = args["data"] + "validation_logs/"
upload_dir = args["data"] + "upload_logs/"
os.makedirs(validation_dir, exist_ok=True)
os.makedirs(upload_dir, exist_ok=True)

filenames = glob.glob(args["data"] + "*.csv") + glob.glob(args["data"] + "*.xlsx")
yml_dict = nh.template_to_dict(args["template"])

conn = psycopg2.connect(**connection, connect_timeout=5)
cur = conn.cursor()

for filename in filenames:
    print(f"Filename: {filename}")
    conn.rollback()
    logfile = []
    databus = {}
    log_dir, log_ext = (
        (upload_dir, ".upload.log") if args["upload"] else (validation_dir, ".valid.log")
    )

    if filename.endswith(".xlsx"):
        csv_file = nh.read_xlsx(filename, num_headers=yml_dict.get("headers", 1))
    else:
        csv_file = nh.read_csv(filename)

    hashcheck = nh.hash_file(filename, validation_files=validation_dir)
    filecheck = nh.check_file(filename, validation_files=validation_dir)
    logfile = logfile + hashcheck["message"] + filecheck["message"]
    logfile.append(f"\nNew Upload started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # An upload needs the file to be unchanged since a clean validation: the hash matches the
    # validation log and that log has no errors. Validation itself is always possible.
    upload_allowed = hashcheck["pass"] and filecheck["pass"]
    if args["upload"] and not upload_allowed:
        logfile.append("File must be properly validated before it can be uploaded.")

    try:
        nh.run_step(
            "Sites", "sites",
            lambda csv_file=csv_file: nv.valid_site(cur=cur, yml_dict=yml_dict, csv_file=csv_file),
            logfile, databus, conn,
        )  # fmt: skip
        nh.run_step(
            "GPUs", "gpuid",
            lambda csv_file=csv_file, databus=databus: nv.valid_geopolitical_units(
                cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus
            ),
            logfile, databus, conn,
        )  # fmt: skip
        nh.run_step(
            "CUs", "collunits",
            lambda csv_file=csv_file, databus=databus: nv.valid_collunit(
                cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus
            ),
            logfile, databus, conn,
        )  # fmt: skip
        nh.run_step(
            "AUs", "analysisunits",
            lambda csv_file=csv_file, databus=databus: nv.valid_analysisunit(
                cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus
            ),
            logfile, databus, conn,
        )  # fmt: skip
        nh.run_step(
            "Datasets", "datasets",
            lambda csv_file=csv_file, databus=databus: nv.valid_dataset(
                cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus
            ),
            logfile, databus, conn,
        )  # fmt: skip
        nh.run_step(
            "Samples", "samples",
            lambda csv_file=csv_file, databus=databus: nv.valid_sample(
                cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus
            ),
            logfile, databus, conn,
        )  # fmt: skip
        nh.run_step(
            "Contacts", "contacts",
            lambda csv_file=csv_file, databus=databus: nv.valid_contact(
                cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus
            ),
            logfile, databus, conn,
        )  # fmt: skip
        nh.run_step(
            "Database", "database",
            lambda databus=databus: nv.valid_dataset_database(cur=cur, yml_dict=yml_dict, databus=databus),
            logfile, databus, conn,
        )  # fmt: skip
        nh.run_step(
            "Data", "data",
            lambda csv_file=csv_file, databus=databus: nv.valid_data(
                cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus
            ),
            logfile, databus, conn,
        )  # fmt: skip

        all_true = all(databus[key].validAll for key in databus)
        if args["upload"]:
            if all_true and upload_allowed:
                databus["finalize"] = nv.insert_final(cur, databus=databus)
                logfile.append("\n === Finalize ===")
                nh.logging_response(databus["finalize"], logfile)
                if databus["finalize"].validAll:
                    conn.commit()
                    logfile.append("Data has been successfully uploaded to the database.")
                else:
                    conn.rollback()
                    logfile.append("Submission could not be finalized.")
            else:
                conn.rollback()
                logfile.append(
                    "Data must be fully validated before it can be uploaded to the database."
                )
        else:
            conn.rollback()
            if all_true:
                logfile.append("Data has been fully validated and is ready for upload.")
            else:
                logfile.append(
                    "Data has not passed validation. Please review the log messages for details."
                )
    except Exception as e:
        conn.rollback()
        logfile.append(f"An error occurred during validation: {str(e)}")

    log_path = log_dir + os.path.basename(filename) + log_ext
    with open(log_path, "w", encoding="utf-8") as writer:
        for line in logfile:
            writer.write(line)
            writer.write("\n")
    print(f"Log written to {log_path}")

conn.close()
