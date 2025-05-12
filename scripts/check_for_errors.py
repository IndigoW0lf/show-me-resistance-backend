import glob
import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# Config
BILL_DIR = "bills/mo/2024-gpt"

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

def main():
    # Get all bill numbers from .md filenames
    files = glob.glob(os.path.join(BILL_DIR, "*.md"))
    all_md_bills = {os.path.basename(f).replace(".md", "").upper() for f in files}

    # Connect and fetch all successfully updated bill_numbers
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.bill_number
        FROM ls_bill b
        JOIN ls_bill_text bt ON b.bill_id = bt.bill_id
        WHERE bt.gpt_summary IS NOT NULL
    """)
    db_bills = {row[0].upper() for row in cursor.fetchall()}
    cursor.close()
    conn.close()

    # Diff
    missing = all_md_bills - db_bills
    print(f"\n📋 Total .md files: {len(all_md_bills)}")
    print(f"✅ Successfully updated in DB: {len(db_bills)}")
    print(f"❌ Missing or failed: {len(missing)}\n")

    for bill in sorted(missing):
        print(f"❌ {bill}")

if __name__ == "__main__":
    main()
    main()
