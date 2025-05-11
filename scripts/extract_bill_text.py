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
