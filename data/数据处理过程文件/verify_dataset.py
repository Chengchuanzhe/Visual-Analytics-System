"""
数据集校验脚本 — 验证最终 JSON 是否符合数据抽象说明书要求
================================================================
检查项（对应 docs/专项文档合集/2-...-数据抽象说明书-A.md）：
  1. 总记录数 = 3600
  2. 字段数 = 16（含 id）
  3. 时间跨度 2020-01-01 ~ 2022-12-31，三年均覆盖
  4. 地域覆盖 6 海域 × 各 600 条（均衡）
  5. 核心字段无 null（time, longitude, latitude, region, sst, salinity）
  6. 数值字段在文档声明的取值范围内
  7. 经度范围 -180 ~ 180

运行：python3 verify_dataset.py
退出码：0 全部通过 / 1 存在问题
"""
import json
import os
import sys
from collections import Counter

DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..",
    "组号-全球海洋大气耦合-实验2-选题扩展数据集.json"
)

EXPECTED_FIELDS = [
    "id", "time", "longitude", "latitude", "region",
    "sst", "salinity", "wind_speed", "wind_dir", "pressure",
    "precipitation", "co2", "wave_height", "humidity",
    "current_speed", "chlorophyll",
]

EXPECTED_REGIONS = ["太平洋", "大西洋", "印度洋", "北极海域", "南极海域", "赤道区域"]

# 字段取值范围（来自数据抽象说明书第三节）
RANGES = {
    "longitude":     (-180,  180),
    "latitude":      ( -82,   82),
    "sst":           (  -2,   32),
    "salinity":      (  30,   38),
    "wind_speed":    ( 0.5,   20),
    "wind_dir":      (   0,  360),
    "pressure":      ( 990, 1035),
    "precipitation": (   0,   10),
    "co2":           ( 405,  425),
    "wave_height":   ( 0.1,    5),
    "humidity":      (  40,  100),
    "current_speed": (0.01,  1.0),
    "chlorophyll":   (0.01,    5),
}

CORE_FIELDS = ["time", "longitude", "latitude", "region", "sst", "salinity"]


def main():
    print(f"加载数据集：{os.path.abspath(DATA_PATH)}")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"  共 {len(data)} 条记录\n")

    failures = []

    # 1. 记录数
    print("[1] 总记录数 == 3600 ?")
    if len(data) == 3600:
        print(f"    ✓ 通过（{len(data)} 条）")
    else:
        msg = f"    ✗ 失败：期望 3600，实际 {len(data)}"
        print(msg); failures.append(msg)

    # 2. 字段数
    print("\n[2] 字段数 == 16 且字段名完整 ?")
    sample = data[0]
    actual_fields = set(sample.keys())
    expected_set = set(EXPECTED_FIELDS)
    missing = expected_set - actual_fields
    extra = actual_fields - expected_set
    if not missing and not extra and len(actual_fields) == 16:
        print(f"    ✓ 通过（16 个字段，全部命中）")
    else:
        msg = f"    ✗ 失败：缺失={missing} 多余={extra}"
        print(msg); failures.append(msg)

    # 3. 时间分布
    print("\n[3] 时间跨度 2020-2022，三年均覆盖 ?")
    years = Counter(d["time"][:4] for d in data if d.get("time"))
    print(f"    年度分布：{dict(years)}")
    if all(years.get(y, 0) > 0 for y in ("2020", "2021", "2022")):
        print(f"    ✓ 通过")
    else:
        msg = f"    ✗ 失败：年度分布不全 {dict(years)}"
        print(msg); failures.append(msg)

    # 4. 海域均衡
    print("\n[4] 6 海域 × 各 600 条 ?")
    region_counts = Counter(d["region"] for d in data)
    all_ok = True
    for r in EXPECTED_REGIONS:
        cnt = region_counts.get(r, 0)
        flag = "✓" if cnt == 600 else "✗"
        print(f"    {flag}  {r:>6s}  {cnt:>4d}")
        if cnt != 600:
            all_ok = False
    extras = set(region_counts) - set(EXPECTED_REGIONS)
    if extras:
        print(f"    ✗ 出现未声明的海域：{extras}")
        all_ok = False
    if all_ok:
        print("    ✓ 通过")
    else:
        failures.append("海域均衡失败")

    # 5. 核心字段无 null
    print("\n[5] 核心字段无 null ?")
    null_counts = {f: 0 for f in CORE_FIELDS}
    for d in data:
        for f in CORE_FIELDS:
            if d.get(f) is None:
                null_counts[f] += 1
    bad = {k: v for k, v in null_counts.items() if v > 0}
    if not bad:
        print(f"    ✓ 通过（{', '.join(CORE_FIELDS)} 均无空值）")
    else:
        msg = f"    ✗ 失败：{bad}"
        print(msg); failures.append(msg)

    # 6. 数值字段范围
    print("\n[6] 数值字段范围 ?")
    range_fail = []
    for f, (lo, hi) in RANGES.items():
        vals = [d[f] for d in data if d.get(f) is not None]
        if not vals:
            continue
        vmin, vmax = min(vals), max(vals)
        in_range = lo <= vmin and vmax <= hi
        flag = "✓" if in_range else "✗"
        print(f"    {flag}  {f:<14s}  实际 [{vmin:>8.3f}, {vmax:>8.3f}]   "
              f"期望 [{lo}, {hi}]")
        if not in_range:
            range_fail.append(f)
    if range_fail:
        msg = f"    ✗ 越界字段：{range_fail}"
        print(msg); failures.append(msg)
    else:
        print("    ✓ 全部字段在期望范围内")

    # 7. 经度范围
    print("\n[7] 经度统一在 -180 ~ 180 ?")
    lons = [d["longitude"] for d in data if d.get("longitude") is not None]
    if all(-180 <= x <= 180 for x in lons):
        print(f"    ✓ 通过（min={min(lons):.2f}, max={max(lons):.2f}）")
    else:
        msg = "    ✗ 存在经度越界值"
        print(msg); failures.append(msg)

    # 总结
    print("\n" + "=" * 60)
    if failures:
        print(f"校验未通过，共 {len(failures)} 项失败：")
        for m in failures:
            print(f"  - {m.strip()}")
        sys.exit(1)
    else:
        print("✓ 全部校验通过 — 数据集符合数据抽象说明书要求。")
        sys.exit(0)


if __name__ == "__main__":
    main()
