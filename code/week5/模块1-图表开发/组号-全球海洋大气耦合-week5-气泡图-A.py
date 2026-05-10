"""
全球海洋-大气耦合 · 多维气泡图 — Python / matplotlib 复现版
==========================================================
对应 HTML 版：组号-全球海洋大气耦合-week5-气泡图-A.html
四维编码：X=SST · Y=Salinity · 大小=Wind Speed · 颜色=海域
配色与 data-adapter.js REGION_COLORS 一致（Okabe-Ito 色盲友好）。

运行：python3 组号-全球海洋大气耦合-week5-气泡图-A.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

plt.rcParams["font.sans-serif"] = ["PingFang HK", "Arial Unicode MS", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_PATH = os.path.join(ROOT, "data",
                         "组号-全球海洋大气耦合-实验2-选题扩展数据集.json")
OUT_PATH = os.path.join(ROOT, "screenshots", "week5", "week5-气泡图-A.png")

# 与 data-adapter.js 一致的 Okabe-Ito 配色
COLORS = {
    "太平洋":   "#0072B2",
    "大西洋":   "#009E73",
    "印度洋":   "#F0E442",
    "北极海域": "#56B4E9",
    "南极海域": "#CC79A7",
    "赤道区域": "#E69F00",
}
REGIONS = ["太平洋", "大西洋", "印度洋", "北极海域", "南极海域", "赤道区域"]

X_KEY, Y_KEY, S_KEY = "sst", "salinity", "wind_speed"
X_LABEL = "海表温度 SST (°C)"
Y_LABEL = "盐度 Salinity (PSU)"
S_LABEL = "风速 Wind Speed (m/s)"


def render():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    clean = [d for d in data
             if d.get(X_KEY) is not None and d.get(Y_KEY) is not None
             and d.get(S_KEY) is not None]

    fig = plt.figure(figsize=(13, 8), dpi=150)
    fig.patch.set_facecolor("#f0f4f8")

    card = fig.add_axes([0.025, 0.03, 0.95, 0.94])
    card.set_xlim(0, 1); card.set_ylim(0, 1); card.axis("off")
    card.add_patch(FancyBboxPatch(
        (0.005, 0.005), 0.99, 0.99,
        boxstyle="round,pad=0.005,rounding_size=0.012",
        linewidth=1, edgecolor="#dde6f0", facecolor="#ffffff",
        transform=card.transAxes))

    card.text(0.03, 0.95, "全球海洋-大气耦合 · 多维气泡图",
              fontsize=15, fontweight="bold", color="#1a2b4a",
              transform=card.transAxes, va="center")
    card.text(0.03, 0.91,
              f"X = {X_LABEL}   ·   Y = {Y_LABEL}   ·   "
              f"气泡大小 = {S_LABEL}   ·   颜色 = 海域",
              fontsize=10.5, color="#5a6b80",
              transform=card.transAxes, va="center")
    card.text(0.97, 0.95,
              f"渲染 {len(clean):,} 条 / 共 {len(data):,} 条",
              fontsize=10, color="#7a8fa6",
              ha="right", transform=card.transAxes, va="center")

    ax = fig.add_axes([0.075, 0.12, 0.70, 0.72])
    ax.set_facecolor("#fbfcfd")
    for spine in ax.spines.values():
        spine.set_color("#c8d6e5")

    xs = np.array([d[X_KEY] for d in clean])
    ys = np.array([d[Y_KEY] for d in clean])
    ws = np.array([d[S_KEY] for d in clean])
    cs = np.array([COLORS[d["region"]] for d in clean])

    w_min, w_max = ws.min(), ws.max()
    r_min_pt, r_max_pt = 4, 28
    radii = r_min_pt + (np.sqrt(ws) - np.sqrt(w_min)) / \
            (np.sqrt(w_max) - np.sqrt(w_min)) * (r_max_pt - r_min_pt)
    sizes = (radii * 2) ** 2 / 4 * np.pi

    ax.grid(True, color="#e8eef5", linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    ax.scatter(xs, ys, s=sizes, c=cs, alpha=0.55,
               edgecolors="white", linewidths=0.6, zorder=2)

    ax.set_xlabel(X_LABEL, fontsize=12, fontweight="bold",
                  color="#2d3e50", labelpad=10)
    ax.set_ylabel(Y_LABEL, fontsize=12, fontweight="bold",
                  color="#2d3e50", labelpad=10)
    ax.tick_params(axis="both", colors="#5a6b80", labelsize=10)

    # 颜色图例
    leg = fig.add_axes([0.79, 0.45, 0.20, 0.40])
    leg.set_xlim(0, 1); leg.set_ylim(0, 1); leg.axis("off")
    leg.text(0.0, 0.97, "海域 (颜色)", fontsize=11, fontweight="bold",
             color="#1a2b4a", transform=leg.transAxes)
    leg.plot([0.0, 0.95], [0.93, 0.93], color="#dde6f0", linewidth=1,
             transform=leg.transAxes)
    yy = 0.85
    for region in REGIONS:
        leg.add_patch(plt.Circle((0.07, yy), 0.035,
                                 color=COLORS[region],
                                 transform=leg.transAxes))
        leg.text(0.18, yy, region, fontsize=11, color="#2d3e50",
                 va="center", transform=leg.transAxes)
        yy -= 0.115

    # 大小图例
    sleg = fig.add_axes([0.79, 0.12, 0.20, 0.30])
    sleg.set_xlim(0, 1); sleg.set_ylim(0, 1); sleg.axis("off")
    sleg.text(0.0, 0.97, "风速 (大小)", fontsize=11, fontweight="bold",
              color="#1a2b4a", transform=sleg.transAxes)
    sleg.plot([0.0, 0.95], [0.93, 0.93], color="#dde6f0", linewidth=1,
              transform=sleg.transAxes)
    sample_ws = [w_min, (w_min + w_max) / 2, w_max]
    yy = 0.78
    for w in sample_ws:
        r = r_min_pt + (np.sqrt(w) - np.sqrt(w_min)) / \
            (np.sqrt(w_max) - np.sqrt(w_min)) * (r_max_pt - r_min_pt)
        radius = r / 380.0
        sleg.add_patch(plt.Circle((0.18, yy), radius,
                                  facecolor="#7a8fa6",
                                  edgecolor="white", linewidth=0.8,
                                  alpha=0.55, transform=sleg.transAxes))
        sleg.text(0.45, yy, f"{w:.1f} m/s", fontsize=10,
                  color="#2d3e50", va="center", transform=sleg.transAxes)
        yy -= 0.25

    card.text(0.5, 0.025,
              "成员 A · 王哲  |  Week 5 模块1  |  气泡图（X+Y+大小+颜色 四维编码）",
              fontsize=9, color="#7a8fa6", ha="center",
              style="italic", transform=card.transAxes)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    plt.savefig(OUT_PATH, dpi=150, facecolor="#f0f4f8",
                bbox_inches="tight", pad_inches=0.15)
    plt.close()
    print(f"[OK] 已生成气泡图截图：{OUT_PATH}")


if __name__ == "__main__":
    render()
