import os
from pathlib import Path

import mysql.connector
import openai
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

openai.api_key = os.getenv("OPENAI_API_KEY")

OUTPUT_DIR = Path("bills/mo/2024-gpt")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def fetch_bills(cursor, limit=None):
    query = """
        SELECT b.bill_number, b.title, b.description, b.legiscan_url, b.state_url,
               bt.bill_id, bt.full_text
        FROM ls_bill_text bt
        JOIN ls_bill b ON b.bill_id = bt.bill_id
        WHERE bt.full_text IS NOT NULL AND bt.gpt_summary IS NULL
    """
    if limit:
        query += " LIMIT %s"
        cursor.execute(query, (limit,))
    else:
        cursor.execute(query)
    return cursor.fetchall()

def generate_gpt_summary(title, bill_number, full_text):
    prompt = f"""
You are a civic analyst writing easy-to-understand, plain-English summaries of government legislation for public transparency.

BILL INFO:
Title: {title}
Bill Number: {bill_number}
Text: {full_text[:4000]}

TASKS:
1. Write a one-sentence summary of this bill for a card-based UI that is easy to understand and thorough.
2. Write a multi-sentence plain-English explanation of what the bill does and who it affects.
3. Provide 3–6 useful tags that describe the bill's topic, impacted groups, policy type, or department.

REPLY IN THIS YAML FORMAT:

summary_short: "..."
summary: |
  ...
tags:
  - ...
  - ...
"""
    response = openai.chat.completions.create(
        model="gpt-4.1-nano-2025-04-14",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def write_summary_file(bill_number, yaml_block):
    filename = f"{bill_number.lower()}.md"
    filepath = OUTPUT_DIR / filename

    # If file exists, skip if identical
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            existing = f.read().strip()
            if existing == yaml_block.strip():
                print(f"⏩ Skipping {bill_number} (no changes)")
                return

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(yaml_block.strip() + "\n")
    print(f"✅ Wrote {filename}")

def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    bills = fetch_bills(cursor)
    print(f"🔍 Found {len(bills)} bills to summarize...\n")

    for bill in bills:
        bill_number = bill["bill_number"]
        title = bill["title"]
        full_text = bill["full_text"]

        print(f"📝 Summarizing {bill_number}: {title[:60]}...")
        try:
            yaml_block = generate_gpt_summary(title, bill_number, full_text)
            write_summary_file(bill_number, yaml_block)
        except Exception as e:
            print(f"❌ Failed on {bill_number}: {e}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()