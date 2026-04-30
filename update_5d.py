import json
import os
from concurrent.futures import ThreadPoolExecutor

# 从你的文件导入价格接口
from get_data import get_price

# ===================== 配置 =====================
INPUT_FILE = "all_history.json"
OUTPUT_FILE = "10d_data.json"
LOOKBACK_DAYS = 10
MAX_WORKERS = 20

# ===================== 加载历史数据 =====================
print(f"📂 正在加载历史数据：{INPUT_FILE}")
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

all_days = data["days"]
recent_days = all_days[-LOOKBACK_DAYS:]
date_list = [d["date"] for d in recent_days]

print(f"✅ 加载完成，获取最近 {LOOKBACK_DAYS} 天数据")
print(f"📅 日期列表：{date_list}")

# 收集所有股票
code_set = set()
for day in recent_days:
    for s in day["stocks"]:
        code_set.add(s["code"])

total_codes = len(code_set)
print(f"🔍 共收集到 {total_codes} 只股票需要处理")

# ===================== 读取已有数据（避免重复拉取） =====================
existing_data = {}
if os.path.exists(OUTPUT_FILE):
    print(f"🔍 检测到已有文件：{OUTPUT_FILE}，尝试读取历史价格...")
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
        print("✅ 已有价格数据读取成功")
    except:
        print("❌ 已有文件读取失败，将重新拉取全部")
        existing_data = {}

existing_prices = existing_data.get("price_map", {})
print(f"📊 已缓存价格数量：{len(existing_prices)} 只股票\n")

# ===================== 多线程获取（不存在才拉） =====================
def fetch_if_missing(code):
    prices = existing_prices.get(code, {})
    skip_count = 0
    fetch_count = 0

    for dt in date_list:
        if dt in prices and prices[dt] not in (None, 0.0, "", 0):
            skip_count += 1
            continue

        try:
            prices[dt] = get_price(code, dt)
            fetch_count += 1
        except:
            prices[dt] = 0.0

    print(f"▸ {code} | 跳过 {skip_count} 条 | 拉取 {fetch_count} 条")
    return code, prices

print(f"🚀 开始多线程拉取价格（线程数：{MAX_WORKERS}）...\n")

# 并发拉取
price_map = {}
with ThreadPoolExecutor(MAX_WORKERS) as executor:
    for code, prices in executor.map(fetch_if_missing, code_set):
        price_map[code] = prices

print(f"\n✅ 所有股票拉取完成！共处理 {len(price_map)} 只股票")

# ===================== 输出新 JSON =====================
print("\n📝 开始生成新JSON结构...")

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

print(f"💾 正在保存文件：{OUTPUT_FILE}")
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# ===================== 最终统计 =====================
print("\n" + "="*50)
print(f"✅ 任务全部完成！")
print(f"📅 日期范围：{date_list[0]} ~ {date_list[-1]}")
print(f"📊 股票总数：{len(code_set)}")
print(f"📁 输出文件：{OUTPUT_FILE}")
print("="*50)
