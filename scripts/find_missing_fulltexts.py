# scripts/find_missing_fulltexts.py
from pathlib import Path

json_dir = Path("bill_texts")
text_dir = Path("bills/mo/2024")

json_basenames = {f.stem.upper() for f in json_dir.glob("*.json")} | {f.stem.upper() for f in json_dir.glob("*.JSON")}
text_basenames = {f.stem.upper().replace("_FULL_TEXT", "") for f in text_dir.glob("*_full_text.md")}

missing = sorted(json_basenames - text_basenames)

print(f"🔍 Found {len(missing)} JSONs without corresponding _full_text.md:")
for bill in missing:
    print(f" - {bill}")
