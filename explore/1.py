import pdfplumber
import glob
import os

os.makedirs("data/raw/txt", exist_ok=True)

for path in sorted(glob.glob("data/raw/pdf/*.pdf")):
    name = os.path.splitext(os.path.basename(path))[0]
    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    out = f"data/raw/txt/{name}.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print("写出:", out)