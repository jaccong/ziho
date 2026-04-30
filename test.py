import json
import os
from concurrent.futures import ThreadPoolExecutor
from get_data import get_price

# ==================== 配置 ====================
INPUT_FILE = "all_history.json"
OUTPUT_FILE = "test_2days_result.json"
TEST_DAYS = 2
MAX_WORKERS = 10

# ==================== 加载数据 ====================
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

all_days = data["days"]
recent_days = all_days[-TEST_DAYS:]
date_list = [d["date"] for d in recent_days]

print("=" * 70)
print(f"📌 测试：最近 2 天价格（多线程）")
print(f"📅 日期：{date_list}")
print("=" * 70)

# 收集股票
codes = set()
for day in recent_days:
    for s in day["stocks"]:
        codes.add(s["code"])
codes = list(codes)

print(f"📊 股票总数：{len(codes)}")
print("=" * 70)

# ==================== 多线程拉取 ====================
def fetch(code):
    res = {}
    print(f"🟢 开始：{code}")
    for dt in date_list:
        try:
            p = get_price(code, dt)
            res[dt] = p
            print(f"   {code} | {dt} → {p}")
            if p in (0, 0.0):
                print(f"   🔴 {code} {dt} = 0（异常）")
        except Exception as e:
            res[dt] = 0.0
            print(f"   🔴 {code} {dt} 错误：{str(e)}")
    return code, res

price_map = {}
with ThreadPoolExecutor(MAX_WORKERS) as executor:
    for code, prices in executor.map(fetch, codes):
        price_map[code] = prices

# ==================== 生成输出 ====================
output = {
    "month": data.get("month"),
    "days": []
}

for day in all_days:
    new_day = {
        "date": day["date"],
        "stocks": []
    }
    for s in day["stocks"]:
        item = s.copy()
        item["price_2d"] = price_map.get(s["code"], {})
        new_day["stocks"].append(item)
    output["days"].append(new_day)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 70)
print("✅ 测试完成！文件：test_2days_result.json")
print("=" * 70)
