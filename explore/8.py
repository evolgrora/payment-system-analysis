import pandas as pd

df = pd.read_csv("data/raw/payment_system.csv")

# 1. 检查缺失与重复
print(df.isna().sum())
print(df.duplicated(subset=["period", "category", "subcategory"]).sum())

# 2. 类型检查（金额列被读成字符串是最常见的坑）
df["count_yi_bi"] = pd.to_numeric(df["count_yi_bi"], errors="coerce")
df["amount_wan_yi"] = pd.to_numeric(df["amount_wan_yi"], errors="coerce")

# 3. 派生核心指标：单笔平均金额（元）
#    万亿元 / 亿笔 = 万元/笔 → ×10000 换成「元/笔」
df["avg_ticket_yuan"] = df["amount_wan_yi"] / df["count_yi_bi"] * 10000

df.to_csv("data/processed/payment_clean.csv", index=False)