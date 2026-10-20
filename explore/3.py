import re

with open("data/raw/txt/pbc_2026Q2.txt", encoding="utf-8") as f:
    raw = f.read()

text = re.sub(r"\s+", "", raw)   # 关键：去掉所有空格和换行
print("规范化后字符数:", len(text))
print("=" * 55)

patterns = {
    "非现金支付": r"非现金支付业务([\d.]+)亿笔，金额([\d.]+)万亿元",
    "银行卡交易": r"银行卡交易([\d.]+)亿笔，金额([\d.]+)万亿元",
    "电子支付":   r"电子支付业务([\d.]+)亿笔，金额([\d.]+)万亿元",
    "网上支付":   r"网上支付业务([\d.]+)亿笔，金额([\d.]+)万亿元",
    "移动支付":   r"移动支付业务([\d.]+)亿笔，金额([\d.]+)万亿元",
    "大额实时":   r"大额实时支付系统处理业务([\d.]+)亿笔，金额([\d.]+)万亿元",
    "小额批量":   r"小额批量支付系统处理业务([\d.]+)亿笔，金额([\d.]+)万亿元",
    "网联清算":   r"网联清算平台处理业务([\d.]+)亿笔，金额([\d.]+)万亿元",
    "CIPS":       r"人民币跨境支付系统处理业务([\d.]+)万笔，金额([\d.]+)万亿元",
}

for name, pat in patterns.items():
    m = re.search(pat, text)
    if m:
        print(f"{name:10s} OK   笔数={m.group(1):>12s}   金额={m.group(2):>12s}")
    else:
        print(f"{name:10s} --   未匹配")
        kw = pat.split("([")[0]
        idx = text.find(kw)
        if idx >= 0:
            print(f"           上下文: {text[max(0, idx - 15): idx + 90]}")
