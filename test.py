import json
import os
from get_data import get_price

# ==================== 配置 ====================
INPUT_FILE  = "all_history.json"
OUTPUT_FILE = "test_2days_result.json"
TEST_DAYS   = 2  # 只测2天

# ==================== 加载 ====================
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

all_days = data["days"]
recent = all_days[-TEST_DAYS:]
dates = [d["date"] for d in recent]

print("="*70)
print(f"📌 测试模式：只拉取最近 {TEST_DAYS} 天")
print(f"📅 测试日期：{dates}")
print("="*70)

# 收集股票
codes = set()
for day in recent:
    for s in day["stocks"]
        codes.add(s["code"])

codes = list(codes)
print(f"📊 本次测试股票总数：{len(codes)}")
print("="*70)

# ==================== 逐个拉取（全开日志） ====================
price_map = {}

for code in codes:
    print(f"\n🟢 正在处理：{code}")
    res = {}

    for dt in dates:
        try:
            p = get_price(code, dt)
            res[dt] = p

            # 关键调试输出
            print(f"   ├─ {dt} → {p}")

            if p == 0 or p == 0.0:
                print(f"   🔴 【异常】价格 = 0")

        except Exception as e:
            res[dt] = 0.0
            print(f"   🔴 【报错】{e}")

    price_map[code] = res

# ==================== 生成测试文件 ====================
output = {
    "month": data.get("month"),
    "days": []
}

for day in all_days:
    new_day = {"date": day["date"], "stocks": []}
    for s in day["stocks"]:
        item = s.copy()
        item["price_2d"] = price_map.get(s["code"], {})
        new_day["stocks"].append(item)
    output["days"].append(new_day)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("\n" + "="*70)
print("✅ 测试完成！文件：test_2days_result.json")
print("🔍 查看上面日志，就能找到哪些【返回0】")
print("="*70)
