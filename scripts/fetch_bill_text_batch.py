import json
from pathlib import Path

import mysql.connector
import requests

# --- Config ---
API_KEY = "ad252f849960a5479826a7941ae7ebd2"
OUTPUT_DIR = Path("bill_texts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LIMIT = 2700  # Only fetch this many to stay safe

# --- MySQL Connection ---
db = mysql.connector.connect(
    host="localhost",
    user="legiscan_api",
    password="Goddess88!Goddess88!",
    database="legiscan_api"
)
cursor = db.cursor(dictionary=True)

# --- Query recent MO bills from 2024 session ---
cursor.execute("""
    SELECT b.bill_number, b.bill_id
    FROM ls_bill b
    JOIN ls_session s ON b.session_id = s.session_id
    JOIN ls_state st ON s.state_id = st.state_id
    WHERE st.state_abbr = 'MO' AND s.year_start = 2024
    ORDER BY b.status_date DESC
    LIMIT %s
""", (LIMIT,))

rows = cursor.fetchall()

for row in rows:
    bill_number = row['bill_number'].upper()
    bill_id = row['bill_id']
    output_path = OUTPUT_DIR / f"{bill_number}.json"

    if output_path.exists():
        print(f"⏩ Already exists: {bill_number}")
        continue

    # Step 1: Get bill details
    bill_url = f"https://api.legiscan.com/?key={API_KEY}&op=getBill&id={bill_id}"
    try:
        bill_response = requests.get(bill_url)
        bill_response.raise_for_status()
        bill_data = bill_response.json()

        if "bill" not in bill_data or "texts" not in bill_data["bill"] or not bill_data["bill"]["texts"]:
            print(f"⚠️ No texts found for {bill_number}")
            continue

        # Grab the first doc_id from the texts list
        doc_id = bill_data["bill"]["texts"][0]["doc_id"]

        # Step 2: Fetch the actual PDF text
        text_url = f"https://api.legiscan.com/?key={API_KEY}&op=getBillText&id={doc_id}"
        text_response = requests.get(text_url)
        text_response.raise_for_status()
        text_data = text_response.json()

        if "text" not in text_data or "doc" not in text_data["text"]:
            print(f"⚠️ No valid 'doc' found for {bill_number}")
            continue

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(text_data, f, indent=2)

        print(f"✅ Fetched and saved: {bill_number}")

    except Exception as e:
        print(f"❌ Failed to fetch {bill_number}: {e}")

cursor.close()
db.close()
db.close()
