# 🛠️ Show Me Resistance — Scripts Pipeline

> A complete overview of all project scripts in the `scripts/` directory, their purpose, and how they relate to each other in the pipeline.

Author: Kai Wolf  
Last updated: 2025-05-11

---

## 📌 Overview

This folder contains all data processing and summarization scripts that support the Show Me Resistance civic transparency pipeline.

Each script plays a role in fetching, extracting, cleaning, summarizing, and exporting legislative data from Missouri's LegiScan API and local MySQL database.

---

## 🧭 Pipeline Order (Chronological Execution Flow)

### 🗂️ Metadata + Initial Markdown

1. **`export-bills-to-md.js`**  
   ⮕ Exports YAML-frontmatter Markdown files with metadata (title, number, sponsor, etc.) from the MySQL `ls_bill` table.

2. **Optional: `clean-bill-frontmatter.js`**  
   ⮕ Wipes frontmatter from Markdown files (if you want to reset for reprocessing).

---

### 📜 PDF ➝ Text ➝ Markdown Prep

3. **`fetch_bill_text_batch.py`**  
   ⮕ Downloads LegiScan `getBillText` JSON files containing base64-encoded bill PDFs for all bills.

4. **`extract_bill_text_dir.py`**  
   ⮕ Extracts plain text from all base64 PDFs into `*_full_text.md` files and optionally injects snippets into the YAML of Markdown files.

5. **`backfill_full_text.py`**  
   ⮕ Reads `./bills/MO/2024/*.md` and inserts their full text into the `ls_bill_text.full_text` database column.

---

### 🧠 GPT Summarization

6. **`generate_gpt_summaries.py`**  
   ⮕ Summarizes all bills that have full text but no GPT summary. Outputs YAML and logs results but does **not** write to the DB.

7. **`summarize_and_save.py`**  
   ⮕ Same as above, but **also updates `ls_bill_text` with `gpt_summary`, `gpt_summary_short`, and `gpt_tags`** after parsing and validation.

---

### 🧪 Utilities and Testing

- **`extract_bill_text.py`**  
  ➤ Extracts full text from a single JSON file (one bill) and writes it to `.md`.

- **`fetch_and_extract.py`**  
  ➤ Fetches and extracts a single bill's text from LegiScan (combined version of `fetch` + `extract`).

- **`inspect_skipped_files.py`**  
  ➤ Lets you visually inspect files that failed parsing (e.g., HCBs or malformed headers).

- **`generate-summaries.js`**  
  ➤ Older Markdown-based GPT summarization script (deprecated in favor of DB versions).

---

## 🔄 Full Workflow (Typical Use)

```text
# 1. Export bill metadata
node export-bills-to-md.js

# 2. Download all bill PDF text JSON
python3 fetch_bill_text_batch.py

# 3. Extract text from PDFs
python3 extract_bill_text_dir.py --markdown-dir ./bills/MO/2024 --fulltext-dir ./recovered-text --json-dir ./cache/doc --output-snippet

# 4. Insert full text into DB
python3 backfill_full_text.py

# 5. Summarize using GPT
python3 summarize_and_save.py

scripts/
├── export-bills-to-md.js
├── clean-bill-frontmatter.js
├── fetch_bill_text_batch.py
├── extract_bill_text_dir.py
├── backfill_full_text.py
├── summarize_and_save.py
├── generate_gpt_summaries.py
├── inspect_skipped_files.py
├── extract_bill_text.py
├── fetch_and_extract.py
├── generate-summaries.js
└── README.md  ← This file!

