# -*- coding: utf-8 -*-
"""
Day 3 · 可视化
读取 data/processed/ 下三张分析表，输出 figures/*.png
每张图回答一个具体问题，结论写在 README.md
"""
import os

import matplotlib
matplotlib.use("Agg")                      # 无界面后端，服务器/命令行也能跑
import matplotlib.pyplot as plt
import pandas as pd

# ---------- 中文字体 ----------
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DengXian"]
plt.rcParams["axes.unicode_minus"] = False

FIG_DIR = "figures"
os.makedirs(FIG_DIR, exist_ok=True)

# ---------- 中文名映射 ----------
NAME = {
    "hvps":          "大额实时支付系统",
    "cips":          "人民币跨境支付系统",
    "bank_internal": "银行行内系统",
    "beps":          "小额批量支付系统",
    "ibps":          "网上支付跨行清算",
    "card":          "银行卡",
    "npl":           "非银网络支付",
    "unionpay":      "银联跨行支付",
    "nuc":           "网联清算平台",
    "ncps":          "非现金支付合计",
    "epay":          "电子支付合计",
}

# epay 有 total / online / mobile 三个子类，单独命名
SUB_NAME = {
    ("epay", "online"): "网上支付",
    ("epay", "mobile"): "移动支付",
    ("epay", "total"):  "电子支付合计",
}


def label(cat: str, sub: str) -> str:
    if cat == "epay" and sub != "total":
        return SUB_NAME[(cat, sub)]
    return NAME.get(cat, cat)


def cn(row) -> str:
    return label(row["category"], row["subcategory"])


# ---------- 载入 ----------
avg  = pd.read_csv("data/processed/avg_ticket.csv")
yoy  = pd.read_csv("data/processed/yoy.csv")
share = pd.read_csv("data/processed/sys_share.csv")

avg["name"] = avg.apply(cn, axis=1)
avg["period"] = avg["period"].astype(str)

# 时间轴排序（2024Q1 -> 2026Q2）
PERIODS = sorted(avg["period"].unique())

LATEST = "2026Q2"
# 参与横截面展示的业务（剔除合计项，避免重复计数）
CROSS = ["hvps", "cips", "bank_internal", "beps", "ibps",
         "card", "unionpay", "nuc", "npl"]
# 参与散点图的业务（口径互不重叠）
YOY_SET = ["hvps", "cips", "bank_internal", "beps", "ibps",
           "card", "unionpay", "nuc", "npl"]

COLOR_UP = "#C0392B"     # 上升用红（中国习惯：涨=红）
COLOR_DOWN = "#1E8449"   # 下降用绿


# =========================================================
# 图 1 · 单笔均值分层（对数坐标）
# 问题：不同清算系统的单笔金额差多少？
# =========================================================
def fig1():
    d = avg[(avg["period"] == LATEST) & (avg["category"].isin(CROSS))].copy()
    d = d.sort_values("avg_ticket_yuan")

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.barh(d["name"], d["avg_ticket_yuan"], color="#2E86C1", height=0.65)

    ax.set_xscale("log")
    ax.set_xlabel("单笔平均金额（元/笔，对数坐标）", fontsize=11)
    ax.set_title(f"{LATEST} 各支付系统单笔平均金额\n跨 4 个数量级：从 235 元到 2485 万元",
                 fontsize=13, pad=14)

    for b, v in zip(bars, d["avg_ticket_yuan"]):
        txt = f"{v:,.0f}" if v < 1e5 else f"{v/1e4:,.0f} 万"
        ax.text(v * 1.15, b.get_y() + b.get_height() / 2, txt,
                va="center", fontsize=9)

    ax.set_xlim(right=d["avg_ticket_yuan"].max() * 3)
    ax.grid(axis="x", alpha=0.3, which="both")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/fig1_avg_ticket.png", dpi=150)
    plt.close(fig)
    print("[OK] fig1_avg_ticket.png")


# =========================================================
# 图 2 · 笔数占比 vs 金额占比（两极背离）
# 问题：谁在承担笔数，谁在承担金额？
# =========================================================
def fig2():
    d = share[(share["period"] == LATEST)].copy()
    d["name"] = d["category"].map(NAME)
    d = d.sort_values("count_share_pct", ascending=False)

    x = range(len(d))
    w = 0.38

    fig, ax = plt.subplots(figsize=(10, 5.8))
    b1 = ax.bar([i - w/2 for i in x], d["count_share_pct"],  w,
                label="笔数占比", color="#5DADE2")
    b2 = ax.bar([i + w/2 for i in x], d["amount_share_pct"], w,
                label="金额占比", color="#E74C3C")

    ax.set_yscale("log")
    ax.set_xticks(list(x))
    ax.set_xticklabels(d["name"], rotation=25, ha="right", fontsize=9)
    ax.set_ylabel("占比（%，对数坐标）", fontsize=11)
    ax.set_title(f"{LATEST} 笔数结构与金额结构严重背离\n"
                 "大额系统 0.02% 的笔数承载 70.77% 的金额",
                 fontsize=13, pad=14)
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3, which="both")
    ax.set_axisbelow(True)
    ax.text(0.99, 0.02, "注：CIPS 笔数占比 0.0005%，对数轴下不可见",
            transform=ax.transAxes, ha="right", fontsize=8.5, color="#777")

    for b, v in zip(b1, d["count_share_pct"]):
        if v > 0.5:
            ax.text(b.get_x() + b.get_width()/2, v * 1.15, f"{v:.2f}",
                    ha="center", fontsize=8.5)
    for b, v in zip(b2, d["amount_share_pct"]):
        if v > 0.5:
            ax.text(b.get_x() + b.get_width()/2, v * 1.15, f"{v:.2f}",
                    ha="center", fontsize=8.5)

    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/fig2_share_divergence.png", dpi=150)
    plt.close(fig)
    print("[OK] fig2_share_divergence.png")


# =========================================================
# 图 3 · 单笔均值指数化趋势（2024Q1 = 100）
# 问题：单笔金额到底在升还是在降？——答案是两端分化
# =========================================================
def fig3():
    watch = [("bank_internal", "total"), ("hvps", "total"),
             ("beps", "total"), ("ibps", "total"),
             ("card", "total"), ("nuc", "total")]

    # 基期用 2024 全年 4 个季度的均值，而不是单个季度——
    # 单季做基期会被季节性扭曲（2024Q1 春节因素使银行卡单笔均值偏高 35%）
    BASE_PERIODS = ["2024Q1", "2024Q2", "2024Q3", "2024Q4"]

    fig, axes = plt.subplots(2, 3, figsize=(13, 6.6), sharey=True)
    axes = axes.ravel()

    up, down = [], []
    for ax, (cat, sub) in zip(axes, watch):
        d = avg[(avg["category"] == cat) & (avg["subcategory"] == sub)]
        d = d.set_index("period").reindex(PERIODS)
        base = d.loc[BASE_PERIODS, "avg_ticket_yuan"].mean()
        idx = d["avg_ticket_yuan"] / base * 100
        name = label(cat, sub)

        last = idx.iloc[-1]
        pct = last - 100
        color = COLOR_UP if pct > 0 else COLOR_DOWN
        (up if pct > 0 else down).append(name)

        ax.plot(range(len(PERIODS)), idx, marker="o", ms=4.5, lw=2.2, color=color)
        ax.fill_between(range(len(PERIODS)), 100, idx, color=color, alpha=0.10)
        ax.axhline(100, color="#999", ls="--", lw=1)

        ax.set_title(f"{name}\n{last:.0f}（{pct:+.1f}%）", fontsize=11,
                     color=color, pad=8)
        ax.set_xticks(range(len(PERIODS)))
        ax.set_xticklabels(PERIODS, rotation=60, fontsize=7.5)
        ax.grid(alpha=0.3)
        ax.set_axisbelow(True)

    lo = min(ax.get_ylim()[0] for ax in axes)
    hi = max(ax.get_ylim()[1] for ax in axes)
    for ax in axes:
        ax.set_ylim(min(lo, 88), max(hi, 112))

    for ax in axes[::3]:
        ax.set_ylabel("指数（2024 全年均值 = 100）", fontsize=10)

    fig.suptitle("单笔金额不是普涨或普跌，而是两端分化（纵轴统一刻度）\n"
                 "上排两格上升 = 批发端；下排四格下降 = 零售端　"
                 "｜基期取 2024 全年四季均值，消除单季季节性",
                 fontsize=12.5, y=1.00)
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/fig3_ticket_index.png", dpi=150)
    plt.close(fig)
    print(f"[OK] fig3_ticket_index.png   上升 {len(up)} 项 / 下降 {len(down)} 项")


# =========================================================
# 图 4 · 笔数同比 vs 金额同比 散点
# 问题：哪些业务在"小额高频"？（落在虚线右下方 = 笔数涨得比金额快）
# =========================================================
def fig4():
    d = yoy[(yoy["period"] == LATEST) &
            (yoy["category"].isin(YOY_SET)) &
            (yoy["subcategory"] == "total")].copy()
    d["name"] = d["category"].map(NAME)

    fig, ax = plt.subplots(figsize=(8.4, 7))
    ax.scatter(d["count_yoy_pct"], d["amount_yoy_pct"],
               s=110, color="#2E86C1", alpha=0.85, edgecolor="white", lw=1.2)

    lim = [min(-8, d["count_yoy_pct"].min() - 4),
           max(22, d["count_yoy_pct"].max() + 4)]
    ax.plot(lim, lim, ls="--", color="#999", lw=1.3)
    ax.text(lim[1] - 1, lim[1] + 0.6, "金额增速 = 笔数增速",
            ha="right", fontsize=9, color="#666")

    # 个别点位密集，标签需要错开
    OFFSET = {
        "npl": (8, -18),
        "ibps": (8, 8),
        "cips": (-78, 14),
        "card": (8, 5),
    }
    for _, r in d.iterrows():
        ax.annotate(r["name"],
                    (r["count_yoy_pct"], r["amount_yoy_pct"]),
                    textcoords="offset points",
                    xytext=OFFSET.get(r["category"], (8, 5)),
                    fontsize=9.5)

    ax.axhline(0, color="#ccc", lw=1)
    ax.axvline(0, color="#ccc", lw=1)
    ax.set_xlabel("笔数同比（%）", fontsize=11)
    ax.set_ylabel("金额同比（%）", fontsize=11)
    ax.set_title(f"{LATEST} 笔数增速与金额增速对比\n"
                 "虚线右下方 = 笔数涨得比金额快 = 小额高频",
                 fontsize=13, pad=14)
    ax.grid(alpha=0.3)
    ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/fig4_yoy_scatter.png", dpi=150)
    plt.close(fig)
    print("[OK] fig4_yoy_scatter.png")


# =========================================================
# 图 5 · 网联 vs 大额实时：两条相反的路
# 问题：小额高频的证据在哪？——网联笔数涨金额跌，大额系统完全相反
# =========================================================
def fig5():
    def series(cat):
        d = yoy[(yoy["category"] == cat) & (yoy["subcategory"] == "total")]
        d = d.set_index("period").reindex(PERIODS)
        return d["count_yoy_pct"], d["amount_yoy_pct"]

    nuc_c, nuc_a = series("nuc")
    hv_c, hv_a = series("hvps")

    # 共享 y 轴：两张图的刻度必须一致，否则右图的波动看起来比左图大
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2), sharey=True)

    # 左：网联
    ax1.plot(PERIODS, nuc_c, marker="o", color=COLOR_UP, lw=2.2, label="笔数同比")
    ax1.plot(PERIODS, nuc_a, marker="s", color=COLOR_DOWN, lw=2.2, label="金额同比")
    ax1.axhline(0, color="#bbb", lw=1)
    ax1.set_title("网联清算平台\n笔数增长、金额回落 → 小额高频的干净证据",
                  fontsize=12)
    ax1.legend(fontsize=9.5)
    ax1.grid(alpha=0.3)
    ax1.tick_params(axis="x", rotation=45)
    ax1.set_ylabel("同比（%）")

    # 右：大额实时
    ax2.plot(PERIODS, hv_c, marker="o", color="#5DADE2", lw=2.2, label="笔数同比")
    ax2.plot(PERIODS, hv_a, marker="s", color="#E74C3C", lw=2.2, label="金额同比")
    ax2.axhline(0, color="#bbb", lw=1)
    ax2.set_title("大额实时支付系统\n金额增速持续高于笔数 → 单笔金额在变大",
                  fontsize=12)
    ax2.legend(fontsize=9.5)
    ax2.grid(alpha=0.3)
    ax2.tick_params(axis="x", rotation=45)

    fig.suptitle("同一时期，两类系统的走向完全相反", fontsize=13.5, y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(f"{FIG_DIR}/fig5_nuc_vs_hvps.png", dpi=150)
    plt.close(fig)
    print("[OK] fig5_nuc_vs_hvps.png")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
    fig5()
    print("\n全部完成，输出目录:", os.path.abspath(FIG_DIR))
