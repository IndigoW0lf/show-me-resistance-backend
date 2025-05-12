"""
inspect_skipped_files.py

DESCRIPTION:
This script is used to quickly inspect the first few lines of any Markdown bill text files
that were skipped during a batch operation—typically during GPT summary backfills or bill number extraction.
The goal is to diagnose formatting inconsistencies or file corruption that caused the file to be ignored.

FUNCTIONALITY:
- Defines a list of filenames that were previously skipped.
- Attempts to open and read the first 5 lines of each file from the Markdown bill text directory.
- Prints a readable preview of each skipped file to standard output.
- Reports any read or encoding failures.

USE CASES:
- Troubleshooting skipped files (e.g., missing bill numbers, formatting issues)
- Manually identifying anomalies in bill files for targeted reprocessing

INPUTS:
- `MARKDOWN_FOLDER`: Path to the bill text files (e.g., `./bills/MO/2024`)
- `SKIPPED_FILES`: Hardcoded list of filenames you want to inspect

OUTPUT:
- Previews printed directly to the terminal

REQUIREMENTS:
- Python 3.x

PIPELINE CONTEXT:
- 🧪 This is a standalone debugging tool, used after processing or summarization scripts
- 🔁 Pairs well with: `backfill_full_text.py`, `extract_bill_number()` failures, or GPT skips

Author: Kai Wolf  
Last updated: 2025-05-11
"""
import os

MARKDOWN_FOLDER = "./bills/MO/2024"
SKIPPED_FILES = [
    "HCB1_full_text.md",
]

print(f"Inspecting {len(SKIPPED_FILES)} skipped files...\n")

for filename in SKIPPED_FILES:
    path = os.path.join(MARKDOWN_FOLDER, filename)
    print(f"🧾 {filename}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for i in range(5):
                line = f.readline()
                if not line:
                    break
                print(f"  {line.strip()}")
        print("—" * 60)
    except Exception as e:
        print(f"❌ Failed to read {filename}: {e}")
        print("—" * 60)
