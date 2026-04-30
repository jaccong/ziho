import json
import os
from concurrent.futures import ThreadPoolExecutor

# 导入你的价格接口
from get_data import get_price

# ===================== 配置 =====================
INPUT_FILE = "all_history.json"
OUTPUT_FILE = "10days_data.json"  # 你要的名称
LOOKBACK_DAYS = 10
MAX_WORKERS = 20

# ===================== 加载原始数据 =====================
print(f"📦 加载原始数据：{INPUT_FILE}")
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

all_days = data["days"]
recent_days = all_days[-LOOKBACK_DAYS:]
date_list = [d["date"] for d in recent_days]

# 收集所有股票
codes = set()
for day in recent_days:
    for s in day["stocks"]:
        codes.add(s["code"])
codes = list(codes)

print(f"✅ 最近10天日期：{' → '.join(date_list)}")
print(f"📊 总股票数量：{len(codes)}")

# ===================== 读取已有的10天价格（避免重复拉）=====================
existing_cache = {}
if os.path.exists(OUTPUT_FILE):
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            old_data = json.load(f)
        
        # 从正确格式读取已缓存价格
        for day in old_data["days"]:
            for stock in day["stocks"]:
                code = stock["code"]
                if "price_10d" in stock:
                    existing_cache[code] = stock["price_10d"]
        print("✅ 成功读取历史缓存，跳过重复数据")
    except:
        existing_cache = {}

# ===================== 拉取逻辑：缺失才拉 =====================
def fetch_stock(code):
    prices = existing_cache.get(code, {})
    for dt in date_list:
        # 已有有效价格 → 跳过
        if dt in prices and prices[dt] not in (None, 0.0, "", 0):
            continue
        # 没有才请求
        try:
            prices[dt] = get_price(code, dt)
        except:
            prices[dt] = 0.0
    return code, prices

# ===================== 多线程获取 =====================
print(f"\n🚀 开始拉取 10 日价格...")
price_map = {}

with ThreadPoolExecutor(MAX_WORKERS) as executor:
    results = executor.map(fetch_stock, codes)
    for code, prices in results:
        price_map[code] = prices

# ===================== 按你原版格式生成 =====================
output = {
    "month": data.get("month", "2026年04月"),
    "days": []
}

# 逐天复制，只加 price_10d，其他完全不变
for day in all_days:
    new_day = {
        "date": day["date"],
        "stocks": []
    }
    for stock in day["stocks"]:
        item = stock.copy()
        item["price_10d"] = price_map.get(stock["code"], {})
        new_day["stocks"].append(item)
    output["days"].append(new_day)

# ===================== 保存新文件 =====================
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n✅ 全部完成！")
print(f"📁 已生成：{OUTPUT_FILE}")
print(f"✅ 格式 100% 匹配你的原始 JSON")
