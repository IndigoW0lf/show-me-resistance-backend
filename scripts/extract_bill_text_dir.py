"""
extract_bill_text_dir.py

DESCRIPTION:
This script extracts the full legislative text from base64-encoded PDFs stored in LegiScan API 
JSON payloads (from `getBillText`) and converts them into plain text `.md` files. Optionally, it 
can inject a snippet of the extracted text into the YAML frontmatter of a companion Markdown file.

FUNCTIONALITY:

1. Reads a directory of Markdown files (`--markdown-dir`) where filenames are matched to 
   bill numbers (e.g. `hb1594.md` ➝ HB1594).
2. Looks for corresponding JSON files in `--json-dir` (named like `HB1594.json`) that were 
   fetched via the `getBillText` LegiScan API endpoint.
3. Extracts the base64-encoded `text.doc` PDF content from the JSON file.
4. Uses `pdfplumber` to decode and extract readable text.
5. Writes the full decoded text to `--fulltext-dir` as `{BILL_NUMBER}_full_text.md`.
6. If `--output-snippet` is passed:
   - It loads the original `.md` file.
   - Inserts a `bill_text` field in the frontmatter with a 10-line preview of the full bill.

REQUIREMENTS:
- Python 3.8+
- `pdfplumber`, `pyyaml`
- LegiScan JSON payloads already fetched and stored locally

USE CASES:
- Prepares clean, text-based versions of official bill documents for summarization, analysis, or frontend previews.
- Helpful when using GPT or search across large bill corpora.
- Supports optional enrichment of existing Markdown files with preview text.

PIPELINE CONTEXT:
- 📥 Run **after** using the `fetch_bill_texts.py` or similar to pull raw `getBillText` JSON responses.
- 📤 Run **before** `backfill_full_text.py` if populating `ls_bill_text.full_text` in the database.
- 🧠 Optional enhancement to `.md` files before feeding to GPT summarization or static site generation.

EXAMPLE USAGE:
```bash
python3 extract_bill_text_dir.py \
  --markdown-dir ./bills/MO/2024 \
  --fulltext-dir ./recovered-text \
  --json-dir ./cache/doc \
  --output-snippet
```

Author: Kai Wolf  
Last updated: 2025-05-11
"""

import argparse
import base64
import io
import json
from pathlib import Path

import pdfplumber
import yaml


def extract_text_from_pdf_base64(base64_str):
    pdf_bytes = base64.b64decode(base64_str)
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

def get_bill_number_from_filename(filename):
    return Path(filename).stem.upper().replace('-', '')  # hb1594.md => HB1594

def main(markdown_dir, fulltext_dir, json_dir, output_snippet):
    markdown_dir = Path(markdown_dir)
    fulltext_dir = Path(fulltext_dir)
    json_dir = Path(json_dir)
    fulltext_dir.mkdir(parents=True, exist_ok=True)

    for md_file in markdown_dir.glob("*.md"):
        bill_number = get_bill_number_from_filename(md_file.name)
        json_path = json_dir / f"{bill_number}.json"

        if not json_path.exists():
            print(f"❌ Missing JSON for {bill_number}")
            continue

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        try:
            doc_base64 = data["text"]["doc"]
        except KeyError:
            print(f"⚠️ No 'doc' field in {json_path.name}")
            continue

        full_text = extract_text_from_pdf_base64(doc_base64)
        text_path = fulltext_dir / f"{bill_number}_full_text.md"
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"📄 Wrote full text for {bill_number}")

        if output_snippet:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            if content.startswith("---"):
                parts = content.split("---", 2)
                frontmatter = yaml.safe_load(parts[1])
                body = parts[2].lstrip()
            else:
                frontmatter = {}
                body = content

            snippet = "\n  ".join(full_text.strip().splitlines()[:10])
            frontmatter["bill_text"] = f"|\n  {snippet}"

            new_content = f"---\n{yaml.safe_dump(frontmatter, sort_keys=False)}---\n{body}"
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"📝 Inserted snippet into {md_file.name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract and insert bill text into Markdown files.")
    parser.add_argument("--markdown-dir", required=True)
    parser.add_argument("--fulltext-dir", required=True)
    parser.add_argument("--json-dir", required=True)
    parser.add_argument("--output-snippet", action="store_true")
    args = parser.parse_args()

    main(
        markdown_dir=args.markdown_dir,
        fulltext_dir=args.fulltext_dir,
        json_dir=args.json_dir,
        output_snippet=args.output_snippet,
    )
