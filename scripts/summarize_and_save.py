import glob
import os
from datetime import datetime

import mysql.connector
import yaml
from dotenv import load_dotenv

load_dotenv()

# === Config ===
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}
BILL_DIR = "bills/mo/2024-gpt"
LOG_FILE = "gpt_summaries.log"

# === Logging ===
def log_result(bill_number, yaml_block):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n\n### {bill_number} ({datetime.now()})\n{yaml_block}")

def log_warning(message):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n⚠️ {datetime.now()} - {message}\n")

# === DB Update ===
def update_gpt_fields(cursor, bill_number, summary_data):
    summary = summary_data.get("summary")
    summary_short = summary_data.get("summary_short")
    tags = summary_data.get("tags", [])

    if not (summary and summary_short and tags):
        print(f"⚠️ Skipping {bill_number}: Missing required fields.")
        return

    tag_string = ", ".join(tags)

    # Check if that specific row already has data
    cursor.execute("""
        SELECT bt.bill_id
        FROM ls_bill_text bt
        JOIN ls_bill b ON b.bill_id = bt.bill_id
        WHERE b.bill_number = %s AND bt.bill_text_type_id = 1
          AND (bt.gpt_summary IS NOT NULL OR bt.gpt_summary_short IS NOT NULL OR bt.gpt_tags IS NOT NULL)
    """, (bill_number,))
    if cursor.fetchone():
        print(f"⏭️ Skipped {bill_number}: Already has GPT fields for introduced version.")
        return

    # Update only the 'introduced' version (bill_text_type_id = 1)
    cursor.execute("""
        UPDATE ls_bill_text
        JOIN ls_bill ON ls_bill.bill_id = ls_bill_text.bill_id
        SET gpt_summary = %s,
            gpt_summary_short = %s,
            gpt_tags = %s
        WHERE ls_bill.bill_number = %s
          AND ls_bill_text.bill_text_type_id = 1
    """, (summary, summary_short, tag_string, bill_number))

    print(f"✅ Updated: {bill_number}")


# === Main workflow ===
def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(buffered=True)

    files = glob.glob(os.path.join(BILL_DIR, "*.md"))
    print(f"📂 Found {len(files)} Markdown files in {BILL_DIR}\n")

    for filepath in files:
        filename = os.path.basename(filepath)
        bill_number = filename.replace(".md", "").upper()

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw_yaml = f.read()
                data = yaml.safe_load(raw_yaml)

            update_gpt_fields(cursor, bill_number, data)

        except Exception as e:
            print(f"❌ Error processing {bill_number}: {e}")
            log_warning(f"Error processing {bill_number}: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("🎉 All Markdown summaries processed.")

if __name__ == "__main__":
    main()
