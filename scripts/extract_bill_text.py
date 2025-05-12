"""
inject_single_bill_text.py

DESCRIPTION:
This script extracts the full text of a **single Missouri bill** from a JSON response 
containing a base64-encoded PDF (`text.doc` field, from LegiScan's `getBillText` API), 
and does two things:

1. Writes the full decoded PDF text to a `_full_text.md` file.
2. Inserts a preview snippet (first 10 lines) into the YAML frontmatter of a matching
   Markdown file (typically created by `export_bill_metadata.js`).

STEPS:
1. Load a `bill_text.json` file containing the API response for one bill.
2. Decode the `text.doc` field (base64 PDF) and extract text using `pdfplumber`.
3. Save the entire plain-text version as `{bill_number}_full_text.md`.
4. Update the corresponding `{bill_number}.md` file by injecting a `bill_text` field 
   into its frontmatter using the first 10 lines as a snippet.
5. Overwrite the `.md` file with the updated content.

REQUIREMENTS:
- Python 3.8+
- `pdfplumber`, `pyyaml`
- JSON file already fetched via `getBillText` API
- Companion `.md` file already created (e.g. by `export_bill_metadata.js`)

TYPICAL USAGE:
- Useful for spot-testing extraction of a single bill.
- Debugging PDF formatting issues before running a batch job.

WHERE IT FITS IN THE PIPELINE:
- 🥇 Comes **after**: You have fetched `getBillText` JSON from LegiScan manually or via script.
- 🥈 Comes **after**: You’ve created the `.md` metadata files via `export_bill_metadata.js`.
- ✅ Use this before backfilling the database or summarizing.

CONFIGURABLE INPUTS:
- `BILL_ID`, `STATE`, `YEAR`: Used to locate the correct files and write paths.
- `JSON_PATH`: Should point to the full-text JSON file.
- `MARKDOWN_PATH`: Should point to the original `.md` file to modify.

Author: Kai Wolf  
Last updated: 2025-05-11
"""

import base64
import io
import json

import pdfplumber
import yaml

# Constants
BILL_ID = "hb1594"
STATE = "mo"
YEAR = "2024"
JSON_PATH = "bill_text.json"
MARKDOWN_PATH = f"bills/{STATE}/{YEAR}/{BILL_ID}.md"
TEXT_EXPORT_PATH = f"bills/{STATE}/{YEAR}/{BILL_ID}_full_text.md"

# Step 1: Load JSON and decode base64 PDF
with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

doc_base64 = data["text"]["doc"]
pdf_bytes = base64.b64decode(doc_base64)

# Step 2: Extract text with pdfplumber
with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
    full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

# Step 3: Optional full text dump
with open(TEXT_EXPORT_PATH, "w", encoding="utf-8") as f:
    f.write(full_text)

# Step 4: Load and update Markdown frontmatter
with open(MARKDOWN_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Separate frontmatter and body
if content.startswith("---"):
    parts = content.split("---", 2)
    frontmatter = yaml.safe_load(parts[1])
    body = parts[2].lstrip()
else:
    frontmatter = {}
    body = content

# Insert truncated bill text into frontmatter
snippet = "\n  ".join(full_text.strip().splitlines()[:10])
frontmatter["bill_text"] = f"|\n  {snippet}"

# Step 5: Write updated Markdown
new_content = f"---\n{yaml.safe_dump(frontmatter, sort_keys=False)}---\n{body}"

with open(MARKDOWN_PATH, "w", encoding="utf-8") as f:
    f.write(new_content)

print("✅ Bill text extracted and inserted into Markdown frontmatter.")
