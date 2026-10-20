"""
从规范化文本提取指标，构建统一口径的原始 CSV。

两个必须容错的现实问题：
  1. 句子中间会插入同比增长/下降，如
     "银行卡交易1180.51亿笔，同比增长5.55%，金额283.89万亿元"
  2. 笔数单位不统一，早期报告大额实时支付系统用"万笔"，后期用"亿笔"
  3. 金额单位有"万亿元"和"亿元"两种

处理办法：单位不从配置读，而是从正则捕获组里取，再按字典换算。

口径统一规则：
  笔数  -> 亿笔    （万笔 / 10000）
  金额  -> 万亿元  （亿元 / 10000）
"""

import csv
import glob
import os
import re
import statistics

BASE = os.path.dirname(os.path.abspath(__file__))
NORM_DIR = os.path.join(BASE, "data", "raw", "norm")
OUT_CSV = os.path.join(BASE, "data", "raw", "payment_system.csv")

COUNT_UNIT = {"亿笔": 1.0, "万笔": 1.0 / 10000}
AMOUNT_UNIT = {"万亿元": 1.0, "亿元": 1.0 / 10000, "万元": 1.0 / 1e8}

FIELDS = [
    ("ncps", "total", "非现金支付业务"),
    ("card", "total", "银行卡交易"),
    ("epay", "total", "电子支付业务"),
    ("epay", "online", "网上支付业务"),
    ("epay", "mobile", "移动支付业务"),
    ("npl", "total", "非银行支付机构处理网络支付业务"),
    ("hvps", "total", "大额实时支付系统处理业务"),
    ("beps", "total", "小额批量支付系统处理业务"),
    ("ibps", "total", "网上支付跨行清算系统处理业务"),
    ("unionpay", "total", "银联跨行支付系统处理业务"),
    ("cips", "total", "人民币跨境支付系统处理业务"),
    ("nuc", "total", "网联清算平台处理业务"),
    ("bank_internal", "total", "银行行内业务系统处理业务"),
]

# 插入语只允许同比/环比，不能用 [^，]* 通配
# 否则会吃掉真正的"金额"，一路匹配到后面的"日均处理业务...，金额"
PATTERN = (
    r"{kw}([\d.]+)(亿笔|万笔)"
    r"(?:，(?:同比|环比)[^，]*)?"
    r"，(?:金额)?([\d.]+)(万亿元|亿元|万元)"
)


def main():
    rows = []
    missing = []

    for path in sorted(glob.glob(os.path.join(NORM_DIR, "*.txt"))):
        name = os.path.splitext(os.path.basename(path))[0]
        period = name.replace("pbc_", "")

        with open(path, encoding="utf-8") as f:
            text = re.sub(r"\s+", "", f.read())

        for cat, sub, kw in FIELDS:
            pat = re.compile(PATTERN.format(kw=re.escape(kw)))
            m = pat.search(text)
            if not m:
                missing.append((period, cat, sub))
                continue

            count = float(m.group(1)) * COUNT_UNIT[m.group(2)]
            amount = float(m.group(3)) * AMOUNT_UNIT[m.group(4)]

            rows.append({
                "period": period,
                "category": cat,
                "subcategory": sub,
                "count_yi_bi": round(count, 6),
                "amount_wan_yi": round(amount, 4),
                "count_unit_raw": m.group(2),
                "amount_unit_raw": m.group(4),
                "source": name,
            })

    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["period", "category", "subcategory",
                           "count_yi_bi", "amount_wan_yi",
                           "count_unit_raw", "amount_unit_raw", "source"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print("写入行数:", len(rows), " / 期望:", len(FIELDS) * 10)
    print("输出:", OUT_CSV)

    if missing:
        print("-" * 50)
        print("仍未匹配:")
        for period, cat, sub in missing:
            print(f"  {period}  {cat}/{sub}")
    else:
        print("全部字段匹配成功")

    # 跨期校验：单笔均值偏离该字段中位数 10 倍以上的，标为可疑
    print("-" * 50)
    print("合理性校验（单笔均值 vs 该字段中位数）:")

    by_key = {}
    for r in rows:
        key = (r["category"], r["subcategory"])
        by_key.setdefault(key, []).append(r["amount_wan_yi"] / r["count_yi_bi"])

    median = {
        k: statistics.median(v) for k, v in by_key.items()
    }

    suspicious = []
    for r in rows:
        key = (r["category"], r["subcategory"])
        ticket = r["amount_wan_yi"] / r["count_yi_bi"]
        med = median[key]
        if med and not (0.1 <= ticket / med <= 10):
            suspicious.append((r["period"], r["category"], ticket, med))

    if suspicious:
        for period, cat, ticket, med in suspicious:
            print(f"  可疑 {period} {cat}: 单笔 {ticket:.4f} 万元, "
                  f"中位数 {med:.4f} 万元")
    else:
        print("  全部通过")

    print("-" * 50)
    last = max(r["period"] for r in rows)
    print(f"{last} 单笔均值抽样:")
    for r in rows:
        if r["period"] == last:
            ticket = r["amount_wan_yi"] / r["count_yi_bi"]
            print(f"  {r['category']:<14} {r['count_yi_bi']:>10.4f} 亿笔  "
                  f"{r['amount_wan_yi']:>9.2f} 万亿元  单笔 {ticket:>12.4f} 万元")


if __name__ == "__main__":
    main()
