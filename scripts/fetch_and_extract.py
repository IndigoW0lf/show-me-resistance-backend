"""
fetch_single_bill_text.py

DESCRIPTION:
This utility script fetches and decodes the full legislative text of a **single bill document**
from the LegiScan API using its `doc_id` (retrieved from a prior `getBill` call's `texts[]` array).

FUNCTIONALITY:

1. Sends a `getBillText` API request using the specified `DOC_ID`.
2. Extracts the `text.doc` field from the API response, which contains a base64-encoded PDF.
3. Decodes the base64 string and extracts readable text from the PDF using `pdfplumber`.
4. Saves the resulting plain text to a local file (`bill_text.txt`).

USE CASES:
- Spot-checking the output of a particular `doc_id`.
- Debugging formatting issues in individual bill PDFs.
- Previewing what text will look like before batch processing or backfilling.

INPUTS:
- `API_KEY`: Your LegiScan API key.
- `DOC_ID`: The `doc_id` value returned from a previous `getBill` API response.

REQUIREMENTS:
- Python 3.8+
- `requests`, `pdfplumber`

TYPICAL PIPELINE ORDER:
- 🥇 Comes **after** calling `getBill` and identifying the appropriate `doc_id`.
- 🧪 Used independently of your batch scripts, often for QA or troubleshooting.

Author: Kai Wolf  
Last updated: 2025-05-11
"""

import base64
import io

import pdfplumber
import requests

API_KEY = "ad252f849960a5479826a7941ae7ebd2"  # your real key
DOC_ID = 2861170  # or whatever bill text doc_id you're working on

url = f"https://api.legiscan.com/?key={API_KEY}&op=getBillText&id={DOC_ID}"
response = requests.get(url)
data = response.json()

# Make sure we got the text key
if "text" not in data or "doc" not in data["text"]:
    raise ValueError("Missing 'text' or 'doc' field in API response")

# Decode base64 string
doc_base64 = data["text"]["doc"]
pdf_bytes = base64.b64decode(doc_base64)

# Extract text using pdfplumber
with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
    full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

# Save output
with open("bill_text.txt", "w", encoding="utf-8") as f:
    f.write(full_text)

print("✅ Bill text extracted and saved to bill_text.txt")
print("✅ Bill text extracted and saved to bill_text.txt")
