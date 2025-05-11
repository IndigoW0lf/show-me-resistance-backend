import requests
import base64
import io
import pdfplumber

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
