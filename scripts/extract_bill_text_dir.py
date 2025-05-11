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
