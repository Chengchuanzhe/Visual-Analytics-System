"""
全球海洋-大气耦合 · 各海域样本分布环形饼图 — Python / matplotlib 复现版
==========================================================
对应 HTML 版：组号-全球海洋大气耦合-week4-饼图-A.html
配色与原 HTML 一致（6 海域），含图例 + 数据标签 + 中心总数。
图片用于实验报告插图，输出到 screenshots/week4/。

运行：python3 组号-全球海洋大气耦合-week4-饼图-A.py
"""
import json
import os
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, FancyBboxPatch, Rectangle
import numpy as np

plt.rcParams["font.sans-serif"] = ["PingFang HK", "Arial Unicode MS", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_PATH = os.path.join(ROOT, "data",
                         "组号-全球海洋大气耦合-实验2-选题扩展数据集.json")
OUT_PATH = os.path.join(ROOT, "screenshots", "week4", "week4-饼图-A.png")

# 与 HTML 版一致的 6 海域配色
COLORS = {
    "太平洋":   "#0077BB",
    "大西洋":   "#33BBEE",
    "印度洋":   "#009988",
    "北极海域": "#EE7733",
    "南极海域": "#CC3311",
    "赤道区域": "#EE3377",
}


def render():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    counts = Counter(d["region"] for d in data)
    total = sum(counts.values())
    pie_data = sorted(counts.items(), key=lambda x: -x[1])

    fig = plt.figure(figsize=(11, 6), dpi=160)
    fig.patch.set_facecolor("#f0f4f8")

    card = fig.add_axes([0.04, 0.04, 0.92, 0.92])
    card.set_xlim(0, 1); card.set_ylim(0, 1); card.axis("off")
    card.add_patch(FancyBboxPatch(
        (0.005, 0.005), 0.99, 0.99,
        boxstyle="round,pad=0.005,rounding_size=0.015",
        linewidth=0, facecolor="#ffffff", transform=card.transAxes))
    card.add_patch(FancyBboxPatch(
        (0.0, 0.0), 1.0, 1.0,
        boxstyle="round,pad=0.0,rounding_size=0.015",
        linewidth=1.2, edgecolor="#dde6f0", facecolor="none",
        transform=card.transAxes))

    card.text(0.04, 0.93, "全球海洋-大气耦合数据集 · 各海域样本分布",
              fontsize=15, fontweight="bold", color="#1a2b4a",
              transform=card.transAxes, va="center")
    card.text(0.04, 0.88,
              f"数据来源：IFREMER Argo 浮标实测（2020–2022）  ·  "
              f"总记录数：{total:,} 条",
              fontsize=10, color="#7a8fa6",
              transform=card.transAxes, va="center")

    # 环形饼图
    pie_ax = fig.add_axes([0.10, 0.10, 0.40, 0.70])
    pie_ax.set_aspect("equal"); pie_ax.axis("off")
    pie_ax.set_xlim(-1.6, 1.6); pie_ax.set_ylim(-1.6, 1.6)

    start = 90.0
    R_OUT, R_IN = 1.20, 0.55
    for region, val in pie_data:
        ang = val / total * 360
        pie_ax.add_patch(Wedge((0, 0), R_OUT, start - ang, start,
                               width=R_OUT - R_IN, facecolor=COLORS[region],
                               edgecolor="white", linewidth=2.5))
        pct = val / total * 100
        if pct > 4:
            mid = np.deg2rad(start - ang / 2)
            pie_ax.text(1.36 * np.cos(mid), 1.36 * np.sin(mid),
                        f"{pct:.1f}%", ha="center", va="center",
                        fontsize=11, fontweight="bold", color="#2d3e50")
        start -= ang

    pie_ax.text(0, 0.18, "总记录数", ha="center", va="center",
                fontsize=11, color="#7a8fa6")
    pie_ax.text(0, -0.10, f"{total:,}", ha="center", va="center",
                fontsize=22, fontweight="bold", color="#1a2b4a")

    # 图例
    leg = fig.add_axes([0.55, 0.10, 0.40, 0.70])
    leg.set_xlim(0, 1); leg.set_ylim(0, 1); leg.axis("off")
    leg.text(0.0, 0.97, "图例", fontsize=12, fontweight="bold",
             color="#1a2b4a", transform=leg.transAxes)
    leg.plot([0.0, 0.95], [0.94, 0.94], color="#dde6f0", linewidth=1,
             transform=leg.transAxes)

    yy = 0.86
    for region, val in pie_data:
        pct = val / total * 100
        leg.add_patch(Rectangle((0.02, yy - 0.025), 0.045, 0.05,
                                facecolor=COLORS[region], edgecolor="none",
                                transform=leg.transAxes))
        leg.text(0.10, yy, region, fontsize=12, fontweight="bold",
                 color="#1a2b4a", va="center", transform=leg.transAxes)
        leg.text(0.62, yy, f"{val:,}", fontsize=12, fontweight="bold",
                 color="#1a2b4a", va="center", ha="right",
                 transform=leg.transAxes)
        leg.text(0.66, yy, f"({pct:.1f}%)", fontsize=11, color="#7a8fa6",
                 va="center", ha="left", transform=leg.transAxes)
        yy -= 0.115

    card.text(0.5, 0.04,
              "成员 A · 王哲  |  Week 4 模块2  |  环形饼图（含图例 + 数据标签）",
              fontsize=9, color="#7a8fa6", ha="center",
              style="italic", transform=card.transAxes)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    plt.savefig(OUT_PATH, dpi=160, facecolor="#f0f4f8",
                bbox_inches="tight", pad_inches=0.15)
    plt.close()
    print(f"[OK] 已生成饼图截图：{OUT_PATH}")


if __name__ == "__main__":
    render()
