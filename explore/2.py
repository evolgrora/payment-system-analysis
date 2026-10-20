with open("data/raw/txt/pbc_2026Q2.txt", encoding="utf-8") as f:
    text = f.read()

for line in text.split("\n"):
    if "非现金支付业务" in line or "大额实时支付系统" in line or "小额批量支付系统" in line:
        print(line)