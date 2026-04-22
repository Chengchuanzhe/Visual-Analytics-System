"""
从 IFREMER ERDDAP 下载 Argo 浮标真实观测数据
数据源：https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats
实测变量：时间、经纬度、海表温度(temp)、盐度(psal)
其余大气变量：基于气候学合理估算
无需注册，直接运行即可
"""

import requests
import json
import math
import random
import time
import sys
from datetime import datetime
from urllib.parse import urlencode

random.seed(0)

ERDDAP_BASE = "https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats.json"

# 6个海域：经纬度范围
REGIONS = [
    {"name": "太平洋",   "lat": (-30,  30), "lon": (150, 210)},
    {"name": "大西洋",   "lat": (-30,  30), "lon": (-60,   0)},
    {"name": "印度洋",   "lat": (-30,  20), "lon": ( 55, 100)},
    {"name": "北极海域", "lat": ( 70,  82), "lon": (  0,  60)},
    {"name": "南极海域", "lat": (-72, -60), "lon": (  0,  60)},
    {"name": "赤道区域", "lat": ( -8,   8), "lon": (200, 260)},
]

def fetch_argo(region):
    """从 IFREMER ERDDAP 下载 Argo 浮标表层数据（pres<=15 dbar ≈ 海表）"""
    lat_lo, lat_hi = region["lat"]
    lon_lo, lon_hi = region["lon"]
    name = region["name"]

    # 手动拼接查询字符串（ERDDAP 的特殊语法）
    variables = "time,latitude,longitude,pres,temp,psal"
    constraints = (
        f"&time>=2020-01-01T00:00:00Z"
        f"&time<=2022-12-31T00:00:00Z"
        f"&pres<=15"
        f"&latitude>={lat_lo}&latitude<={lat_hi}"
        f"&longitude>={lon_lo}&longitude<={lon_hi}"
    )
    url = f"{ERDDAP_BASE}?{variables}{constraints}"

    print(f"  正在下载 [{name}] ...", end=" ", flush=True)
    try:
        resp = requests.get(url, timeout=180)
        resp.raise_for_status()
        data = resp.json()
        rows = data["table"]["rows"]
        print(f"获取 {len(rows)} 条原始记录")
        return rows
    except Exception as e:
        print(f"失败：{e}")
        return []

def estimate_atmo(lat, lon, date_str):
    """
    根据纬度/季节估算大气变量（气候学合理值）
    """
    month = int(date_str[5:7])
    lat_r = math.radians(abs(lat))
    season = math.sin(2 * math.pi * (month - 1) / 12)

    year = int(date_str[:4])
    wind_speed    = round(max(0.5, random.gauss(6 + 3 * math.sin(lat_r), 2)), 2)
    wind_dir      = round(random.uniform(0, 360), 1)
    pressure      = round(random.gauss(1013 - 3 * math.sin(lat_r * 2), 5), 1)
    precipitation = round(max(0, random.gauss(3 - 2 * math.sin(lat_r), 1.5)), 2)
    co2           = round(random.gauss(413 + 2.5 * (year - 2020), 3), 2)
    wave_height   = round(max(0.1, random.gauss(1.5 + 0.5 * math.sin(lat_r), 0.6)), 2)
    humidity      = round(min(100, max(40, random.gauss(78 - 10 * math.sin(lat_r), 8))), 1)
    current_speed = round(max(0.01, random.gauss(0.3 + 0.1 * season, 0.15)), 3)
    chlorophyll   = round(max(0.01, random.gauss(0.8 + 1.2 * math.sin(lat_r), 0.5)), 3)

    return {
        "wind_speed":    wind_speed,
        "wind_dir":      wind_dir,
        "pressure":      pressure,
        "precipitation": precipitation,
        "co2":           co2,
        "wave_height":   wave_height,
        "humidity":      humidity,
        "current_speed": current_speed,
        "chlorophyll":   chlorophyll,
    }

def build_record(record_id, region_name, row):
    time_raw, lat, lon, pres, temp, psal = row
    date_str = time_raw[:10] if time_raw else "2020-01-01"

    # 经度规范化到 -180~180
    if lon is not None and lon > 180:
        lon = lon - 360

    atmo = estimate_atmo(lat or 0, lon or 0, date_str)
    return {
        "id":            record_id,
        "time":          date_str,
        "longitude":     round(lon, 4) if lon is not None else None,
        "latitude":      round(lat, 4) if lat is not None else None,
        "region":        region_name,
        "sst":           round(temp, 2) if temp is not None else None,  # 实测 (°C)
        "salinity":      round(psal, 2) if psal is not None else None,  # 实测 (PSU)
        **atmo,
    }

def main():
    all_records = []

    for region in REGIONS:
        rows = fetch_argo(region)
        if not rows:
            print(f"  [{region['name']}] 无数据，跳过")
            continue

        # 过滤掉缺失关键字段的行，再随机采样最多 600 条
        valid = [r for r in rows if None not in (r[0], r[1], r[2], r[4])]
        if len(valid) > 600:
            valid = random.sample(valid, 600)

        for row in valid:
            all_records.append(build_record(len(all_records) + 1, region["name"], row))

        print(f"    → 已保留 {len(valid)} 条有效记录（累计 {len(all_records)}）")
        time.sleep(1)  # 礼貌性限速

    if len(all_records) < 100:
        print("\n数据量不足，请检查网络连接或稍后重试。")
        sys.exit(1)

    # 重新编 id
    for i, r in enumerate(all_records):
        r["id"] = i + 1

    out = "../../data/组号-全球海洋大气耦合-实验2-选题扩展数据集.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 完成！共 {len(all_records)} 条记录 → {out}")
    print(f"  字段数：{len(all_records[0])} 个")
    print(f"  地域覆盖：{sorted({r['region'] for r in all_records})}")
    print(f"  时间跨度：{sorted({r['time'][:4] for r in all_records})}")

if __name__ == "__main__":
    main()
