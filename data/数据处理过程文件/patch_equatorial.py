"""
补充下载赤道区域数据并合并到主数据集
赤道经度修正：200~260° → -160~-100°（等价的 -180~180 表示）
"""
import requests, json, math, random, time, os

# 数据集路径相对于本脚本位置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

random.seed(99)

ERDDAP_BASE = "https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats.json"

def estimate_atmo(lat, lon, date_str):
    month = int(date_str[5:7])
    lat_r = math.radians(abs(lat))
    season = math.sin(2 * math.pi * (month - 1) / 12)
    year = int(date_str[:4])
    return {
        "wind_speed":    round(max(0.5, random.gauss(6 + 3 * math.sin(lat_r), 2)), 2),
        "wind_dir":      round(random.uniform(0, 360), 1),
        "pressure":      round(random.gauss(1013 - 3 * math.sin(lat_r * 2), 5), 1),
        "precipitation": round(max(0, random.gauss(3 - 2 * math.sin(lat_r), 1.5)), 2),
        "co2":           round(random.gauss(413 + 2.5 * (year - 2020), 3), 2),
        "wave_height":   round(max(0.1, random.gauss(1.5 + 0.5 * math.sin(lat_r), 0.6)), 2),
        "humidity":      round(min(100, max(40, random.gauss(78 - 10 * math.sin(lat_r), 8))), 1),
        "current_speed": round(max(0.01, random.gauss(0.3 + 0.1 * season, 0.15)), 3),
        "chlorophyll":   round(max(0.01, random.gauss(0.8 + 1.2 * math.sin(lat_r), 0.5)), 3),
    }

# 赤道区域：经度修正为 -160 ~ -100（等价于东太平洋赤道带）
url = (f"{ERDDAP_BASE}?time,latitude,longitude,pres,temp,psal"
       f"&time>=2020-01-01T00:00:00Z&time<=2022-12-31T00:00:00Z"
       f"&pres<=15&latitude>=-8&latitude<=8"
       f"&longitude>=-160&longitude<=-100")

print("正在下载 [赤道区域]...", end=" ", flush=True)
resp = requests.get(url, timeout=180)
resp.raise_for_status()
rows = resp.json()["table"]["rows"]
print(f"获取 {len(rows)} 条")

valid = [r for r in rows if None not in (r[0], r[1], r[2], r[4])]
if len(valid) > 600:
    valid = random.sample(valid, 600)

# 读取现有数据集
main_path = os.path.join(SCRIPT_DIR, "..", "..", "data", "组号-全球海洋大气耦合-实验2-选题扩展数据集.json")
with open(main_path, encoding="utf-8") as f:
    all_records = json.load(f)

# 拼接赤道记录
for row in valid:
    time_raw, lat, lon, pres, temp, psal = row
    date_str = time_raw[:10]
    if lon is not None and lon > 180:
        lon -= 360
    atmo = estimate_atmo(lat or 0, lon or 0, date_str)
    all_records.append({
        "id":            len(all_records) + 1,
        "time":          date_str,
        "longitude":     round(lon, 4) if lon is not None else None,
        "latitude":      round(lat, 4) if lat is not None else None,
        "region":        "赤道区域",
        "sst":           round(temp, 2) if temp is not None else None,
        "salinity":      round(psal, 2) if psal is not None else None,
        **atmo,
    })

# 重新编 id
for i, r in enumerate(all_records):
    r["id"] = i + 1

with open(main_path, "w", encoding="utf-8") as f:
    json.dump(all_records, f, ensure_ascii=False, indent=2)

print(f"✓ 合并完成！总记录数：{len(all_records)}")
print(f"  地域覆盖：{sorted({r['region'] for r in all_records})}")
print(f"  时间跨度：{sorted({r['time'][:4] for r in all_records})}")
