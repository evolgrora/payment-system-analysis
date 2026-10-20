"""
从央行《支付体系运行总体情况》PDF 提取干净的正文文本。

关键点：脚注的字号明显小于正文。按字号过滤掉脚注字符，
可以避免脚注编号污染正文数字（如把 3282.71 变成 113282.71）。

输出两份：
  data/raw/txt_clean/{name}.txt  段落版，保留换行，供人工核对
  data/raw/norm/{name}.txt       规范化版，每句一行，供正则提取
"""

import glob
import os
import re
from collections import Counter

import pdfplumber

BASE = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE, "data", "raw", "pdf")
OUT_TXT = os.path.join(BASE, "data", "raw", "txt_clean")
OUT_NORM = os.path.join(BASE, "data", "raw", "norm")

os.makedirs(OUT_TXT, exist_ok=True)
os.makedirs(OUT_NORM, exist_ok=True)


def extract_without_footnotes(pdf_path):
    """提取正文，按字号过滤脚注。"""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            chars = page.chars
            if not chars:
                continue
            sizes = [round(c["size"], 1) for c in chars]
            body_size = Counter(sizes).most_common(1)[0][0]

            keep = page.filter(
                lambda obj, b=body_size: not (
                    obj.get("object_type") == "char"
                    and obj.get("size", b) < b - 0.3
                )
            )
            pages.append(keep.extract_text() or "")
    return "\n".join(pages)


def to_paragraphs(text):
    """段落版：去掉行内空格与空行，保留换行结构。"""
    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t\u3000]+", "", line)
        if line:
            lines.append(line)
    return "\n".join(lines)


def to_normalized(text):
    """规范化版：去掉全部空白并按句号切分，每句一行。"""
    one = re.sub(r"\s+", "", text)
    sentences = re.split(r"(?<=。)", one)
    return "\n".join(s.strip() for s in sentences if s.strip())


def main():
    pdfs = sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
    print("待处理 PDF 数量:", len(pdfs))
    print("-" * 50)

    for path in pdfs:
        name = os.path.splitext(os.path.basename(path))[0]
        raw = extract_without_footnotes(path)

        with open(os.path.join(OUT_TXT, name + ".txt"), "w", encoding="utf-8") as f:
            f.write(to_paragraphs(raw))

        with open(os.path.join(OUT_NORM, name + ".txt"), "w", encoding="utf-8") as f:
            f.write(to_normalized(raw))

        print(f"{name}  正文字符数 {len(raw)}")

    print("-" * 50)
    print("段落版 ->", OUT_TXT)
    print("规范化版 ->", OUT_NORM)


if __name__ == "__main__":
    main()
