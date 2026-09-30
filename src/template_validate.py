import os
import json
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
import DataBUS.neotomaValidator as nv
import DataBUS.neotomaHelpers as nh
from DataBUS.neotomaHelpers.logging_dict import logging_response

load_dotenv()
connection = json.loads(os.getenv('PGDB_TANK'))

# ── Configure your data pairs here ────────────────────────────────────────────
# Uncomment the pair you want to test:

data = {'csv_templates': ['data/CZ_makro_short.csv'],
        'yml_templates': ['src/templates/template.yml']}

# filenames = glob.glob(args["data"] + "*.csv") + glob.glob(args["data"] + "*.xlsx")

# data = {'csv_templates': ['data/Pollen_Nick/LV2_pollen_combined_wide.csv'],
#         'yml_templates': ['data/Pollen_Nick/wide_template.yaml']}


conn = psycopg2.connect(**connection, connect_timeout=5)
cur = conn.cursor()

for filename, yml in zip(data['csv_templates'], data['yml_templates']):
    print(f"Filename: {filename}")
    conn.rollback()
    logfile = []
    databus = dict()

    yml_dict = nh.template_to_dict(yml)

    if filename.endswith(".xlsx"):
        csv_file = nh.read_xlsx(filename, num_headers=yml_dict.get("headers", 1))
    else:
        csv_file = nh.read_csv(filename)

    hashcheck = nh.hash_file(filename)
    filecheck = nh.check_file(filename, validation_files="data/")

    logfile = logfile + hashcheck['message'] + filecheck['message']
    logfile.append(f"\nNew Upload started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if hashcheck['pass'] is False and filecheck['pass'] is False:
        logfile.append("File must be properly validated before it can be uploaded.")
        hashcheck = False
    else:
        hashcheck = True

    try:
        logfile.append("=== Sites ===")
        result = nh.safe_step("sites", lambda: nv.valid_site(
            cur=cur, yml_dict=yml_dict, csv_file=csv_file), logfile, conn)
        if result is not None:
            databus['sites'] = result
            logfile = logging_response(databus['sites'], logfile)
        print(databus['sites'])
        logfile.append("=== GPUs ===")
        result = nh.safe_step("gpus", lambda: nv.valid_geopolitical_units(
            cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        if result is not None:
            databus['gpuid'] = result
            logfile = logging_response(databus['gpuid'], logfile)

        logfile.append("=== CUs ===")
        result = nh.safe_step("collunits", lambda: nv.valid_collunit(
            cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        if result is not None:
            databus['collunits'] = result
            logfile = logging_response(databus['collunits'], logfile)

        # logfile.append("=== Speleothems ===")
        # result = nh.safe_step("speleothems", lambda: nv.valid_speleothem(
        #     cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        # if result is not None:
        #     databus['speleothems'] = result
        #     logfile = logging_response(databus['speleothems'], logfile)

        # logfile.append("=== External Speleothems ===")
        # result = nh.safe_step("external_speleo", lambda: nv.valid_external_speleothem(
        #     cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        # if result is not None:
        #     databus['external_speleo'] = result
        #     logfile = logging_response(databus['external_speleo'], logfile)
    
        logfile.append("=== AUs ===")   
        result = nh.safe_step("analysisunits", lambda: nv.valid_analysisunit(
            cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        if result is not None:
            databus['analysisunits'] = result
            logfile = logging_response(databus['analysisunits'], logfile)

        # if "210pb" in filename.lower():
        #     logfile.append("=== Pb Models ===")
        #     result = nh.safe_step("pbmodel", lambda: nv.valid_pbmodel(
        #         cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        #     if result is not None:
        #         databus['pbmodel'] = result
        #         logfile = logging_response(databus['pbmodel'], logfile)

        logfile.append("=== Datasets ===")
        result = nh.safe_step("datasets", lambda: nv.valid_dataset(
            cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        if result is not None:
            databus['datasets'] = result
            logfile = logging_response(databus['datasets'], logfile)

        # # only for SISAL and 210Pb
        # if "sisal" in filename.lower() or "210pb" in filename.lower():
        #     logfile.append("=== GeoDS ===")
        #     result = nh.safe_step("geodataset", lambda: nv.valid_geochron_dataset(
        #         cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        #     if result is not None:
        #         databus['geodataset'] = result
        #         logfile = logging_response(databus['geodataset'], logfile)

        # if "node" not in filename.lower():
        #     logfile.append("=== Chronologies ===")
        #     result = nh.safe_step("chronologies", lambda: nv.valid_chronologies(
        #         cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        #     if result is not None:
        #         databus['chronologies'] = result
        #         logfile = logging_response(databus['chronologies'], logfile)

            # logfile.append("=== Chron Controls ===")
            # result = nh.safe_step("chron_controls", lambda: nv.valid_chroncontrols(
            #     cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
            # if result is not None:
            #     databus['chron_controls'] = result
            #     logfile = logging_response(databus['chron_controls'], logfile)
        
        # if "sisal" in filename.lower():
        #     logfile.append("=== Hiatus ===")
        #     result = nh.safe_step("hiatus", lambda: nv.valid_hiatus(
        #         cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        #     if result is not None:
        #         databus['hiatus'] = result
        #         logfile = logging_response(databus['hiatus'], logfile)

        logfile.append("=== Samples ===")
        result = nh.safe_step("samples", lambda: nv.valid_sample(
            cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        if result is not None:
            databus['samples'] = result
            logfile = logging_response(databus['samples'], logfile)

        # if "node" not in filename.lower():
        #     logfile.append("=== Sample Ages ===")
        #     result = nh.safe_step("sample_age", lambda: nv.valid_sample_age(
        #         cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        #     if result is not None:
        #         databus['sample_age'] = result
        #         logfile = logging_response(databus['sample_age'], logfile)

            # logfile.append("=== Geochron ===")
            # result = nh.safe_step("geochron", lambda: nv.valid_geochron(
            #     cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
            # if result is not None:
            #     databus['geochron'] = result
            #     logfile = logging_response(databus['geochron'], logfile)

            # logfile.append("=== Geochron Control ===")
            # result = nh.safe_step("geochroncontrol", lambda: nv.valid_geochroncontrol(
            #     cur=cur, databus=databus), logfile, conn)
            # if result is not None:
            #     databus['geochroncontrol'] = result
            #     logfile = logging_response(databus['geochroncontrol'], logfile)
        
        # if "210pb" in filename.lower():
        #     logfile.append("=== UTh Series ===")
        #     result = nh.safe_step("uthseries", lambda: nv.valid_uth_series(
        #         cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        #     if result is not None:
        #         databus['uthseries'] = result
        #         logfile = logging_response(databus['uthseries'], logfile)

        # logfile.append("=== Contacts ===")
        # result = nh.safe_step("contacts", lambda: nv.valid_contact(
        #     cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        # if result is not None:
        #     databus['contacts'] = result
        #     logfile = logging_response(databus['contacts'], logfile)

        # logfile.append("=== Database ===")
        # result = nh.safe_step("database", lambda: nv.valid_dataset_database(
        #     cur=cur, yml_dict=yml_dict, databus=databus), logfile, conn)
        # if result is not None:
        #     databus['database'] = result
        #     logfile = logging_response(databus['database'], logfile)

        logfile.append("=== Data ===")
        result = nh.safe_step("data", lambda: nv.valid_data(
            cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        if result is not None:
            databus['data'] = result
            logfile = logging_response(databus['data'], logfile)

        # if "210pb" in filename.lower():
        #     logfile.append("=== Data Uncertainty ===")
        #     result = nh.safe_step("uncertainty", lambda: nv.valid_datauncertainty(
        #         cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        #     if result is not None:
        #         databus['uncertainty'] = result
        #         logfile = logging_response(databus['uncertainty'], logfile)

        # # ── aeDNA-specific steps ──────────────────────────────────────────
        # if "aeDNA" in filename.lower():
        #     logfile.append("=== Sequences & aeDNA Models ===")
        #     result = nh.safe_step("sequences", lambda: nv.valid_sequence(
        #         cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        #     if result is not None:
        #         databus['sequences'] = result
        #         logfile = logging_response(databus['sequences'], logfile)

        #     logfile.append("=== Projects ===")
        #     result = nh.safe_step("project", lambda: nv.valid_project(
        #         cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        #     if result is not None:
        #         databus['project'] = result
        #         logfile = logging_response(databus['project'], logfile)

        # logfile.append("=== Publications ===")
        # result = nh.safe_step("publications", lambda: nv.valid_publication(
        #     cur=cur, yml_dict=yml_dict, csv_file=csv_file, databus=databus), logfile, conn)
        # if result is not None:
        #     databus['publications'] = result
        #     logfile = logging_response(databus['publications'], logfile)

        all_true = all([databus[key].validAll for key in databus])
        all_true = all_true and hashcheck
        upload = False
        if upload:
            if all_true:
                databus['finalize'] = nv.insert_final(cur, databus=databus)
                conn.rollback()
                logfile.append("Data has been successfully uploaded to the database.")
            else:
                conn.rollback()
                logfile.append("Data must be fully validated before it can be uploaded to the database.")
        else:
            if all_true:
                conn.rollback()
                logfile.append("Data has been fully validated and is ready for upload.")
            else:
                conn.rollback()
                logfile.append("Data has not passed validation. Please review the log messages for details.")
    except Exception as e:
        conn.rollback()
        logfile.append(f"An error occurred during validation: {str(e)}")
    with open(filename + '.valid.log', 'w', encoding="utf-8") as writer:
        for i in logfile:
            writer.write(i)
            writer.write('\n')
