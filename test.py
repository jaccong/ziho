import json
import os
from concurrent.futures import ThreadPoolExecutor
from get_data import get_price,print_error_report

# ========== 配置 ==========
INPUT_FILE  = "all_history.json"
OUTPUT_FILE = "alldays_data.json"
MAX_WORKERS = 50

# ========== 1. 加载 ==========
print("📦 加载数据...")
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)

days = raw["days"]
date_list = [d["date"] for d in days]
date_set = set(date_list)

print(f"📅 总交易日数: {len(date_list)}")

# ========== 2. 缓存 ==========
cache = {}
if os.path.exists(OUTPUT_FILE):
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            old = json.load(f)
        for d in old["days"]:
            for s in d["stocks"]:
                cache[s["code"]] = s.get("price_10d", {})
        print("♻️ 已加载缓存")
    except:
        cache = {}

# ========== 3. 建立股票 → 出现日期 ==========
stock_first = {}
for d in days:
    dt = d["date"]
    for s in d["stocks"]:
        code = s["code"]
        if code not in stock_first:
            stock_first[code] = dt

print(f"📊 股票数: {len(stock_first)}")

# ========== 4. 预处理：每只股票的有效日期 ==========
stock_valid_dates = {}
for code, first_dt in stock_first.items():
    stock_valid_dates[code] = [d for d in date_list if d >= first_dt]

# ========== 5. 构建缺失任务（核心优化） ==========
tasks = []  # (code, dt)

for code, valid_dates in stock_valid_dates.items():
    existed = cache.get(code, {})
    for dt in valid_dates:
        if dt not in existed or existed.get(dt) in (0, None, "", 0.0):
            tasks.append((code, dt))

print(f"🚀 待请求次数: {len(tasks)}")

# ========== 6. 扁平化请求函数 ==========
def fetch(task):
    code, dt = task
    try:
        price = get_price(code, dt)
    except:
        price = 0.0
    return code, dt, price

# ========== 7. 批量请求 ==========
result_map = {}

print("⚡ 开始请求...")
with ThreadPoolExecutor(MAX_WORKERS) as exe:
    for code, dt, price in exe.map(fetch, tasks):
        if code not in result_map:
            result_map[code] = {}
        result_map[code][dt] = price

# ========== 8. 合并缓存 ==========
for code, data in result_map.items():
    if code not in cache:
        cache[code] = {}
    cache[code].update(data)

# ========== 9. 输出 ==========
out = {
    "month": raw.get("month", ""),
    "days": []
}

for d in days:
    new_day = {
        "date": d["date"],
        "stocks": []
    }
    for s in d["stocks"]:
        new_stock = s.copy()
        new_stock["price_10d"] = cache.get(s["code"], {})
        new_day["stocks"].append(new_stock)
    out["days"].append(new_day)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print_error_report()
print("\n✅ 完成")
print(f"📁 输出: {OUTPUT_FILE}")
print(f"⚡ 请求量已优化（只请求缺失数据）")
