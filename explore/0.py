import pdfplumber
import glob
import os

files = sorted(glob.glob("data/raw/pdf/*.pdf"))
print("找到 PDF 数量:", len(files))

for path in files:
    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    print(f"{os.path.basename(path):22s} 字符数 {len(text)}")
