import json
import os
from concurrent.futures import ThreadPoolExecutor

# 从你的文件导入价格接口
from get_data import get_price

# ===================== 配置 =====================
INPUT_FILE = "all_history.json"
OUTPUT_FILE = "10d_data.json"
LOOKBACK_DAYS = 10  # 👈 这里改成 10 就变成10天
MAX_WORKERS = 20

# ===================== 加载历史数据 =====================
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

all_days = data["days"]
recent_days = all_days[-LOOKBACK_DAYS:]
date_list = [d["date"] for d in recent_days]

# 收集所有股票
code_set = set()
for day in recent_days:
    for s in day["stocks"]:
        code_set.add(s["code"])

# ===================== 读取已有数据（避免重复拉取） =====================
existing_data = {}
if os.path.exists(OUTPUT_FILE):
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    except:
        existing_data = {}

existing_prices = existing_data.get("price_map", {})

# ===================== 多线程获取（不存在才拉） =====================
def fetch_if_missing(code):
    prices = existing_prices.get(code, {})

    for dt in date_list:
        # 👀 核心：已经有价格了，就不再拉！
        if dt in prices and prices[dt] not in (None, 0.0, "", 0):
            continue

        try:
            prices[dt] = get_price(code, dt)
        except:
            prices[dt] = 0.0

    return code, prices

# 并发拉取
price_map = {}
with ThreadPoolExecutor(MAX_WORKERS) as executor:
    for code, prices in executor.map(fetch_if_missing, code_set):
        price_map[code] = prices

# ===================== 输出新 JSON =====================
output = {
    "generated_at": os.popen("date +'%Y-%m-%d %H:%M:%S'").read().strip(),
    "lookback_days": LOOKBACK_DAYS,
    "dates": date_list,
    "price_map": price_map,
    "days": []
}

# 按天补齐数据
for day in recent_days:
    day_out = {
        "date": day["date"],
        "stocks": []
    }
    for s in day["stocks"]:
        code = s["code"]
        day_out["stocks"].append({
            "code": code,
            "name": s["name"],
            "lianban": s["lianban"],
            "sector": s["sector"],
            "close": s["close"],
            "prices_10d": price_map.get(code, {})
        })
    output["days"].append(day_out)

# 保存
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✅ 10天价格更新完成：{OUTPUT_FILE}")
print(f"📅 日期范围：{date_list[0]} ~ {date_list[-1]}")
print(f"📊 股票总数：{len(code_set)}")
