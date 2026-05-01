import json
import os
from concurrent.futures import ThreadPoolExecutor
from get_data import get_price

# ========== 配置 ==========
INPUT_FILE  = "all_history.json"
OUTPUT_FILE = "10days_data.json"
WINDOW_NUM  = 10
MAX_WORKERS = 20

# ========== 1. 加载原始数据 ==========
print("📦 加载原始行情文件...")
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)

# 只截取【最新10个交易日】，直接砍掉前面所有旧日期
last_10_days = raw["days"][-WINDOW_NUM:]
date_list = [item["date"] for item in last_10_days]

print(f"✅ 已锁定最新 {WINDOW_NUM} 个交易日：")
print(f"📅 日期范围：{date_list[0]} ~ {date_list[-1]}")

# ========== 2. 加载已有缓存，避免重复抓取 ==========
cache = {}
if os.path.exists(OUTPUT_FILE):
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            old = json.load(f)
        for day in old["days"]:
            for stock in day["stocks"]:
                if "price_10d" in stock:
                    cache[stock["code"]] = stock["price_10d"]
        print("✅ 读取历史缓存，已有价格自动跳过")
    except:
        cache = {}

# ========== 3. 记录每只股票在10天窗口内首次出现日期 ==========
stock_first = {}
for day_item in last_10_days:
    d = day_item["date"]
    for s in day_item["stocks"]:
        code = s["code"]
        if code not in stock_first:
            stock_first[code] = d

print(f"📊 窗口内共需处理个股：{len(stock_first)} 只")

# ========== 4. 单只股票抓取逻辑 ==========
def fetch(code):
    first_dt = stock_first[code]
    prices = cache.get(code, {})

    # 只遍历这10天，从个股首次出现那天往后取
    for dt in date_list:
        # 还没到它上市那天，直接跳过
        if dt < first_dt:
            continue
        # 已有有效价格，跳过
        if dt in prices and prices[dt] not in (0, 0.0, None, ""):
            continue
        # 接口抓取
        try:
            prices[dt] = get_price(code, dt)
        except:
            prices[dt] = 0.0
    return code, prices

# ========== 5. 多线程批量抓取 ==========
print("\n🚀 开始多线程抓取行情...")
price_map = {}
with ThreadPoolExecutor(MAX_WORKERS) as exe:
    for code, p in exe.map(fetch, stock_first.keys()):
        price_map[code] = p

# ========== 6. 只生成最新10天的JSON（彻底去掉4月1日旧数据） ==========
out = {
    "month": raw.get("month", ""),
    "days": []
}

# 只循环最后10天，不碰前面旧数据
for day_item in last_10_days:
    new_day = {
        "date": day_item["date"],
        "stocks": []
    }
    for s in day_item["stocks"]:
        new_stock = s.copy()
        new_stock["price_10d"] = price_map.get(s["code"], {})
        new_day["stocks"].append(new_stock)
    out["days"].append(new_day)

# ========== 7. 保存 ==========
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("\n✅ 完成！")
print(f"📁 输出文件：{OUTPUT_FILE}")
print(f"✅ 只保留最新10个交易日，已剔除4月1日等旧数据")
print(f"✅ 每只个股仅从自身出现日期往后取值，不浪费请求")
