"""
backfill_full_text.py

DESCRIPTION:
This script scans a directory of Markdown files (e.g. ./bills/MO/2024) containing full bill text 
scraped or decoded from PDF sources and backfills that content into the `ls_bill_text.full_text` 
column in a MySQL database.

It performs the following:

1. Loads and parses each .md file in the specified folder.
2. Uses a flexible regex to extract the bill number (e.g., HB1594, HJR122) from the text body—
   even across line breaks (e.g. "HOUSE JOINT\nRESOLUTION").
3. Checks whether that bill already has a `full_text` in the database:
   - If yes, skips it.
   - If not, updates the corresponding row in `ls_bill_text`.
4. Logs all updates and skips (with reasons) to `backfill_log.txt`.

NOTES:
- Supports all bill types: HB, SB, HR, SR, HJR, SJR, HCR, SCR, HCB.
- Automatically detects and logs missing JSON mappings or invalid bill IDs.
- Appends a log of every run with timestamp and skip/update summaries.

REQUIREMENTS:
- Python 3.8+
- `mysql-connector-python`, `python-dotenv`
- A valid `.env` file with DB credentials and a `config.local.ini` file mimicking PHP-style INI.

PIPELINE CONTEXT:
- 🧾 Run this **after** decoding and extracting PDF text into Markdown files (e.g., with `extract_bill_text_dir.py`)
- 🏛️ Populates `ls_bill_text.full_text`, which is **required** before running `summarize_and_save_gpt.py`
- 🔁 Can be safely re-run; it skips records already populated
- 🧼 Markdown files can be deleted after this runs successfully

TYPICAL USE:
Used to bulk insert actual legislative text into the SQL database for later summarization, display, or analysis.

AUTHOR: Kai Wolf  
LAST UPDATED: 2025-05-11
"""


import configparser
import os
import re
from datetime import datetime

import mysql.connector
from dotenv import load_dotenv

# === Logging setup ===
LOG_PATH = "backfill_log.txt"
log_lines = []
skipped_files = []


def log(msg):
    print(msg)
    log_lines.append(msg)

# === Load environment ===
load_dotenv()

# === Load config ===
config = configparser.ConfigParser()
config.read("config.local.ini")

dsn = config["database"]["dsn"]
user = config["database"]["db_user"]
password = os.getenv("DB_PASSWORD") if config["database"]["db_pass"] == "__FROM_ENV__" else config["database"]["db_pass"]

# === Parse DSN ===
dsn_parts = dict(part.split("=") for part in dsn.split(":")[1].split(";"))
host = dsn_parts.get("host", "localhost")
port = int(dsn_parts.get("port", 3306))
database = dsn_parts["dbname"]

DB_CONFIG = {
    "host": host,
    "port": port,
    "user": user,
    "password": password,
    "database": database,
}

MARKDOWN_FOLDER = "./bills/MO/2024"

# === Helper functions ===
def extract_bill_number(text):
    # Normalize input to a single line so we catch things like:
    # "HOUSE JOINT\nRESOLUTION NO. 123"
    text = " ".join(line.strip() for line in text.splitlines())

    match = re.search(
        r"(HOUSE|SENATE)\s+(COMMITTEE\s+BILL|BILL|RESOLUTION|JOINT\s+RESOLUTION|CONCURRENT\s+RESOLUTION)[^\d]*(\d+)",
        text,
        re.IGNORECASE
    )

    if match:
        chamber = match.group(1).upper()
        type_ = match.group(2).upper().replace(" ", "_")
        number = match.group(3)

        prefix_map = {
            ("HOUSE", "BILL"): "HB",
            ("SENATE", "BILL"): "SB",
            ("HOUSE", "RESOLUTION"): "HR",
            ("SENATE", "RESOLUTION"): "SR",
            ("HOUSE", "JOINT_RESOLUTION"): "HJR",
            ("SENATE", "JOINT_RESOLUTION"): "SJR",
            ("HOUSE", "CONCURRENT_RESOLUTION"): "HCR",
            ("SENATE", "CONCURRENT_RESOLUTION"): "SCR",
            ("HOUSE", "COMMITTEE_BILL"): "HCB",
        }

        prefix = prefix_map.get((chamber, type_))
        if prefix:
            return f"{prefix}{number}"

    return None

def clean_text(text):
    return text.strip()

def get_bill_id_and_current_text(cursor, bill_number):
    cursor.execute(
        "SELECT bt.bill_id, bt.full_text FROM ls_bill b "
        "JOIN ls_bill_text bt ON b.bill_id = bt.bill_id "
        "WHERE b.bill_number = %s", (bill_number,))
    result = cursor.fetchone()
    while cursor.nextset():
        pass
    return result

def update_full_text(cursor, bill_id, full_text):
    cursor.execute(
        "UPDATE ls_bill_text SET full_text = %s WHERE bill_id = %s",
        (full_text, bill_id)
    )

def backfill_full_text():
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(buffered=True)

    updated = 0
    skipped = 0

    for filename in os.listdir(MARKDOWN_FOLDER):
        if not filename.endswith(".md"):
            continue

        file_path = os.path.join(MARKDOWN_FOLDER, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            content = " ".join(line.strip() for line in f.readlines())

        bill_number = extract_bill_number(content)
        if not bill_number:
          msg = f"❌ Skipping {filename}: No bill number found."
          log(msg)
          skipped += 1
          skipped_files.append(filename)
          continue

        result = get_bill_id_and_current_text(cursor, bill_number)
        if not result:
            log(f"❌ Skipping {filename}: No matching bill_id found for {bill_number}.")
            skipped += 1
            continue

        bill_id, existing_text = result
        if existing_text and existing_text.strip():
            log(f"⏩ Skipping {bill_number}: full_text already populated.")
            skipped += 1
            continue

        full_text = clean_text(content)
        if len(full_text) < 100:
            log(f"⚠️  Warning for {bill_number}: text appears unusually short.")

        update_full_text(cursor, bill_id, full_text)
        log(f"✅ Backfilled full_text for {bill_number} (bill_id={bill_id}).")
        updated += 1

    connection.commit()
    cursor.close()
    connection.close()

    summary = f"\n🎉 Backfill complete: {updated} updated, {skipped} skipped."
    log(summary)

    # === Write to log file ===
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if skipped_files:
      log("\n📂 Skipped files with no recognized bill number:")
      for fname in skipped_files:
          log(f" - {fname}")

    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(f"\n--- Backfill Run @ {timestamp} ---\n")
        for line in log_lines:
            log_file.write(line + "\n")

if __name__ == "__main__":
    backfill_full_text()
    backfill_full_text()
