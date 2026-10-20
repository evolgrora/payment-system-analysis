import re

with open("data/raw/txt/pbc_2026Q2.txt", encoding="utf-8") as f:
    raw = f.read()

text = re.sub(r"\s+", "", raw)

for kw in ["网联清算平台处理业务", "人民币跨境支付系统处理业务"]:
    idx = text.find(kw)
    print("=" * 60)
    if idx < 0:
        print(kw, "→ 关键词都没找到")
        continue
    print("关键词:", kw)
    print("后 200 字:", text[idx: idx + 200])
