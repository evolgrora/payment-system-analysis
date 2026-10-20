"""
Day 2：用 DuckDB 写 SQL 生成三张分析表。

1. avg_ticket   单笔平均金额（元/笔），按类别 × 季度
2. yoy          同比增速（笔数、金额），同比 = 与四个季度前比
3. sys_share    支付系统内部结构占比（笔数占比 vs 金额占比）

注意：结构占比只在支付系统组内算，不能把所有类别混在一起加总，
      因为 ncps（非现金支付合计）已经包含了 card / epay，会重复计算。
"""

import os

import duckdb

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "data", "raw", "payment_system.csv").replace("\\", "/")
OUT = os.path.join(BASE, "data", "processed")

os.makedirs(OUT, exist_ok=True)

con = duckdb.connect()
con.execute(f"""
    CREATE OR REPLACE TABLE payment AS
    SELECT * FROM read_csv_auto('{RAW}')
""")

# ---------- 1. 单笔平均金额 ----------
con.execute("""
    CREATE OR REPLACE TABLE avg_ticket AS
    SELECT
        period,
        category,
        subcategory,
        count_yi_bi,
        amount_wan_yi,
        ROUND(amount_wan_yi / count_yi_bi * 10000, 2) AS avg_ticket_yuan
    FROM payment
""")

# ---------- 2. 同比增速（与四个季度前比） ----------
con.execute("""
    CREATE OR REPLACE TABLE yoy AS
    SELECT
        period,
        category,
        subcategory,
        count_yi_bi,
        amount_wan_yi,
        ROUND(
            (count_yi_bi / LAG(count_yi_bi, 4) OVER (
                PARTITION BY category, subcategory ORDER BY period) - 1) * 100
        , 2) AS count_yoy_pct,
        ROUND(
            (amount_wan_yi / LAG(amount_wan_yi, 4) OVER (
                PARTITION BY category, subcategory ORDER BY period) - 1) * 100
        , 2) AS amount_yoy_pct
    FROM payment
""")

# ---------- 3. 支付系统内部结构占比 ----------
con.execute("""
    CREATE OR REPLACE TABLE sys_share AS
    WITH sys AS (
        SELECT * FROM payment
        WHERE category IN ('hvps', 'beps', 'ibps', 'unionpay', 'nuc', 'cips', 'bank_internal')
    )
    SELECT
        period,
        category,
        count_yi_bi,
        amount_wan_yi,
        ROUND(count_yi_bi / SUM(count_yi_bi) OVER (PARTITION BY period) * 100, 2) AS count_share_pct,
        ROUND(amount_wan_yi / SUM(amount_wan_yi) OVER (PARTITION BY period) * 100, 2) AS amount_share_pct
    FROM sys
""")

for name in ["avg_ticket", "yoy", "sys_share"]:
    path = os.path.join(OUT, name + ".csv")
    con.execute(f"COPY {name} TO '{path.replace(chr(92), '/')}' (HEADER, DELIMITER ',')")
    print("写出:", path)

# ---------- 关键结论预览 ----------
print("=" * 70)
print("结论一：单笔均值是否在降（万元/笔，取每年 Q2 对比口径）")
print(con.execute("""
    SELECT category, subcategory,
           ROUND(MAX(CASE WHEN period = '2024Q2' THEN avg_ticket_yuan END) / 10000, 4) AS "2024Q2",
           ROUND(MAX(CASE WHEN period = '2025Q2' THEN avg_ticket_yuan END) / 10000, 4) AS "2025Q2",
           ROUND(MAX(CASE WHEN period = '2026Q2' THEN avg_ticket_yuan END) / 10000, 4) AS "2026Q2",
           ROUND(
               (MAX(CASE WHEN period = '2026Q2' THEN avg_ticket_yuan END)
              / MAX(CASE WHEN period = '2024Q2' THEN avg_ticket_yuan END) - 1) * 100
           , 1) AS "两年变化%"
    FROM avg_ticket
    GROUP BY category, subcategory
    ORDER BY "2026Q2" DESC NULLS LAST
""").df().to_string(index=False))

print("=" * 70)
print("结论二：最新一期 笔数占比 vs 金额占比（支付系统组内）")
print(con.execute("""
    SELECT category, count_share_pct, amount_share_pct,
           ROUND(amount_share_pct - count_share_pct, 2) AS gap_pct
    FROM sys_share
    WHERE period = '2026Q2'
    ORDER BY amount_share_pct DESC
""").df().to_string(index=False))

print("=" * 70)
print("结论三：2026Q2 同比增速（笔数 vs 金额，单位 %）")
print(con.execute("""
    SELECT category, subcategory, count_yoy_pct, amount_yoy_pct,
           ROUND(count_yoy_pct - amount_yoy_pct, 2) AS count_minus_amount
    FROM yoy
    WHERE period = '2026Q2'
    ORDER BY count_minus_amount DESC NULLS LAST
""").df().to_string(index=False))
