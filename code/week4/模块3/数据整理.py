"""
=============================================================================
  全球海洋-大气耦合时空可视分析系统 — 数据整理工具
  成员 C | Week 4 模块3

  功能：
    1. 数据集加载与基本信息统计
    2. 按海域/年份/月份分组聚合
    3. 各维度数值分布摘要（min/max/mean/median/std）
    4. 缺失值与异常值检测
    5. 图表适配：导出饼图/散点图/桑基图/雷达图所需的数据格式
    6. 时间序列提取（按海域、按变量）
    7. 相关性矩阵计算（海洋-大气变量耦合分析）
=============================================================================
"""

import json
import os
import sys
import math
from collections import defaultdict

# ────────────────────────────────────────────────────────────────
#  0. 路径配置
# ────────────────────────────────────────────────────────────────
DATASET_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "data",
    "组号-全球海洋大气耦合-实验2-选题扩展数据集.json"
)


# ────────────────────────────────────────────────────────────────
#  1. 数据加载
# ────────────────────────────────────────────────────────────────
def load_data(path=None):
    """加载 JSON 数据集，返回列表。"""
    path = path or DATASET_PATH
    if not os.path.exists(path):
        print(f"[错误] 数据文件不存在: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"[OK] 已加载 {len(data)} 条记录")
    return data


# ────────────────────────────────────────────────────────────────
#  2. 基本信息统计
# ────────────────────────────────────────────────────────────────
def summary(data):
    """打印数据集整体摘要，返回数值字段和类别字段名列表。"""
    if not data:
        return [], []
    print("\n" + "=" * 60)
    print("  数据集整体摘要")
    print("=" * 60)

    print(f"  总记录数:      {len(data)}")
    print(f"  总字段数:      {len(data[0])}")
    print(f"  海域数:        {len(set(d['region'] for d in data))}")
    print(f"  海域分布:      {sorted(set(d['region'] for d in data))}")

    dates = sorted(d["time"] for d in data if d.get("time"))
    print(f"  时间跨度:      {dates[0]} ~ {dates[-1]}")
    print(f"  覆盖年份:      {sorted(set(d[:4] for d in dates))}")

    numeric_fields = [k for k, v in data[0].items()
                      if isinstance(v, (int, float)) and k != "id"]
    string_fields = [k for k, v in data[0].items() if isinstance(v, str)]
    print(f"  数值字段 ({len(numeric_fields)}): {numeric_fields}")
    print(f"  类别字段 ({len(string_fields)}):  {string_fields}")

    return numeric_fields, string_fields


# ────────────────────────────────────────────────────────────────
#  3. 按海域分组统计
# ────────────────────────────────────────────────────────────────
def region_stats(data, fields=None):
    """按海域分组，对每个数值字段计算 mean/min/max/std/median。"""
    if fields is None:
        fields = [k for k, v in data[0].items()
                  if isinstance(v, (int, float)) and k != "id"]

    print("\n" + "=" * 60)
    print("  各海域数值维度统计（均值 ± 标准差）")
    print("=" * 60)

    regions = sorted(set(d["region"] for d in data))
    result = {}

    for region in regions:
        subset = [d for d in data if d["region"] == region]
        result[region] = {}
        print(f"\n  [{region}] — {len(subset)} 条")

        for field in fields:
            values = [d[field] for d in subset if d.get(field) is not None]
            if not values:
                continue
            mean_val = sum(values) / len(values)
            sorted_vals = sorted(values)
            median_val = sorted_vals[len(sorted_vals) // 2]
            std_val = math.sqrt(
                sum((v - mean_val) ** 2 for v in values) / len(values)
            )
            result[region][field] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": round(mean_val, 4),
                "median": round(median_val, 4),
                "std": round(std_val, 4),
            }
            print(f"    {field:20s}: "
                  f"μ={mean_val:8.2f}  [{min(values):.2f}, {max(values):.2f}]  "
                  f"σ={std_val:.2f}")

    return result


# ────────────────────────────────────────────────────────────────
#  4. 数据质量检查
# ────────────────────────────────────────────────────────────────
def quality_check(data):
    """检查缺失值与 3σ 异常值。"""
    print("\n" + "=" * 60)
    print("  数据质量检查")
    print("=" * 60)

    numeric_fields = [k for k, v in data[0].items()
                      if isinstance(v, (int, float)) and k != "id"]

    for field in numeric_fields:
        values = [d[field] for d in data if d.get(field) is not None]
        null_count = sum(1 for d in data if d.get(field) is None)

        if null_count > 0:
            print(f"  [警告] {field}: {null_count} 条缺失")

        if len(values) > 1:
            mean_val = sum(values) / len(values)
            std_val = math.sqrt(
                sum((v - mean_val) ** 2 for v in values) / len(values)
            )
            outliers = [v for v in values if abs(v - mean_val) > 3 * std_val]
            if outliers:
                print(f"  [信息] {field}: {len(outliers)} 个 3σ 外异常值")

    print("  [OK] 质量检查完成")


# ────────────────────────────────────────────────────────────────
#  5. 相关性矩阵
# ────────────────────────────────────────────────────────────────
def correlation_matrix(data, fields=None):
    """
    计算数值字段之间的 Pearson 相关系数矩阵。
    用于分析海洋与大气变量之间的耦合强度。
    """
    if fields is None:
        fields = [k for k, v in data[0].items()
                  if isinstance(v, (int, float)) and k != "id"]

    # 提取完整矩阵（无缺失值）
    matrix = []
    for d in data:
        row = [d.get(f) for f in fields]
        if None not in row:
            matrix.append(row)

    print("\n" + "=" * 60)
    print("  海洋-大气变量相关系数矩阵（Pearson r）")
    print("=" * 60)

    # 表头
    print(f"  {'':>16s}", end="")
    for f in fields:
        print(f"{f:>10s}", end="")
    print()

    for i, fi in enumerate(fields):
        print(f"  {fi:>16s}", end="")
        for j, fj in enumerate(fields):
            xi = [row[i] for row in matrix]
            xj = [row[j] for row in matrix]
            r = _pearson(xi, xj)
            print(f"{r:10.3f}", end="")
        print()

    return matrix


def _pearson(x, y):
    """计算 Pearson 相关系数。"""
    n = len(x)
    if n < 3:
        return 0
    mx = sum(x) / n
    my = sum(y) / n
    sx = math.sqrt(sum((v - mx) ** 2 for v in x))
    sy = math.sqrt(sum((v - my) ** 2 for v in y))
    if sx == 0 or sy == 0:
        return 0
    return sum((x[i] - mx) * (y[i] - my) for i in range(n)) / (sx * sy)


# ────────────────────────────────────────────────────────────────
#  6. 图表数据导出
# ────────────────────────────────────────────────────────────────

def export_for_pie(data):
    """导出饼图格式：海域 → 记录数。"""
    regions = sorted(set(d["region"] for d in data))
    return [{"category": r, "value": sum(1 for d in data if d["region"] == r)}
            for r in regions]


def export_for_scatter(data, x_key="sst", y_key="humidity"):
    """导出散点图格式：[{x, y, region, time, id}]。"""
    return [
        {"x": d.get(x_key), "y": d.get(y_key),
         "region": d["region"], "time": d["time"], "id": d["id"]}
        for d in data
        if d.get(x_key) is not None and d.get(y_key) is not None
    ]


def export_for_radar(data):
    """
    导出雷达图格式：
    每个海域一条记录，维度为各数值字段的 0-100 归一化均值。
    """
    fields = [k for k, v in data[0].items()
              if isinstance(v, (int, float)) and k != "id"
              and k not in ("longitude", "latitude")]

    regions = sorted(set(d["region"] for d in data))
    result = {}
    g_min = {f: float("inf") for f in fields}
    g_max = {f: float("-inf") for f in fields}

    for region in regions:
        subset = [d for d in data if d["region"] == region]
        result[region] = {}
        for f in fields:
            vals = [d[f] for d in subset if d.get(f) is not None]
            if vals:
                m = sum(vals) / len(vals)
                result[region][f] = m
                g_min[f] = min(g_min[f], m)
                g_max[f] = max(g_max[f], m)

    normalized = []
    for region in regions:
        entry = {"region": region}
        for f in fields:
            rng = g_max[f] - g_min[f]
            entry[f] = round(
                (result[region][f] - g_min[f]) / rng * 100, 2
            ) if rng > 0 else 50
        normalized.append(entry)

    return {"fields": fields, "data": normalized}


def export_for_sankey(data):
    """
    导出桑基图格式：海域 → 年份 流向。
    """
    regions = sorted(set(d["region"] for d in data))
    years = sorted(set(d["time"][:4] for d in data))

    nodes = [{"name": r} for r in regions] + \
            [{"name": y + "年"} for y in years]
    name_to_idx = {n["name"]: i for i, n in enumerate(nodes)}

    links = []
    for region in regions:
        for year in years:
            count = sum(1 for d in data
                        if d["region"] == region and d["time"][:4] == year)
            if count > 0:
                links.append({
                    "source": name_to_idx[region],
                    "target": name_to_idx[year + "年"],
                    "value": count,
                })

    return {"nodes": nodes, "links": links}


# ────────────────────────────────────────────────────────────────
#  7. 时间序列聚合
# ────────────────────────────────────────────────────────────────
def time_series(data, field, by="month", region=None):
    """
    提取时间序列数据。
    by: "month" | "year" | "day"
    region: 指定海域，None=全部
    """
    subset = [d for d in data if region is None or d["region"] == region]

    groups = defaultdict(list)
    for d in subset:
        if d.get(field) is None:
            continue
        key = d["time"]
        if by == "year":
            key = key[:4]
        elif by == "month":
            key = key[:7]  # YYYY-MM

        groups[key].append(d[field])

    return sorted(
        [{"time": k, "mean": sum(v)/len(v),
          "min": min(v), "max": max(v), "count": len(v)}
         for k, v in groups.items()],
        key=lambda x: x["time"]
    )


# ────────────────────────────────────────────────────────────────
#  8. 主程序
# ────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  全球海洋-大气耦合数据整理工具 v1.0")
    print("  成员 C | Week 4 模块3")
    print("=" * 60)

    data = load_data()
    if not data:
        print("请检查数据集路径后重试。")
        return

    num_fields, _ = summary(data)
    quality_check(data)
    region_stats(data, num_fields[:6])  # 仅前 6 个数值字段
    correlation_matrix(data, num_fields[:6])

    # 图表导出示例
    print("\n" + "=" * 60)
    print("  图表数据导出示例")
    print("=" * 60)

    pie_data = export_for_pie(data)
    print(f"  饼图数据: {json.dumps(pie_data, ensure_ascii=False)}")

    radar = export_for_radar(data)
    print(f"  雷达图维度数: {len(radar['fields'])}")
    print(f"  雷达图海域: {[d['region'] for d in radar['data']]}")

    sankey = export_for_sankey(data)
    print(f"  桑基图: {len(sankey['nodes'])} 节点, {len(sankey['links'])} 边")

    # 时间序列示例
    print("\n  时间序列 (SST, 按月聚合, 前 5 条):")
    ts = time_series(data, "sst", by="month")[:5]
    for point in ts:
        print(f"    {point['time']}: μ={point['mean']:.2f}°C")

    print("\n  [完成] 数据整理完毕。")


if __name__ == "__main__":
    main()
