import json
import os
from concurrent.futures import ThreadPoolExecutor
from get_data import get_price

# ===================== 配置 =====================
INPUT_FILE = "all_history.json"
OUTPUT_FILE = "10days_data.json"
MAX_WORKERS = 20
WINDOW_DAYS = 10   # 固定最近10个交易日

# ===================== 1. 加载原始数据 =====================
print("📦 加载 all_history.json ...")
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

all_days_list = raw_data["days"]
# 从文件末尾倒取 10 个真实交易日（完全跟着你json走，不自己算日期）
latest_10_day_objs = all_days_list[-WINDOW_DAYS:]
# 窗口内的日期数组（从小到大）
window_date_set = {d["date"] for d in latest_10_day_objs}
window_start_date = latest_10_day_objs[0]["date"]
window_end_date = latest_10_day_objs[-1]["date"]

print(f"✅ 锁定最近 {WINDOW_DAYS} 个交易日窗口：")
print(f"📅 窗口起始：{window_start_date}")
print(f"📅 窗口结束：{window_end_date}")

# 全部日期映射：date -> 当天股票
date_stock_map = {d["date"]: d["stocks"] for d in all_days_list}

# ===================== 2. 读取历史缓存，避免重复拉取 =====================
cache_price_map = {}
if os.path.exists(OUTPUT_FILE):
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            old_out = json.load(f)
        # 从旧输出里提取每只股票已有的 price_10d
        for day in old_out["days"]:
            for stock in day["stocks"]:
                code = stock["code"]
                if "price_10d" in stock:
                    cache_price_map[code] = stock["price_10d"]
        print("✅ 加载历史价格缓存，已有数据自动跳过")
    except:
        cache_price_map = {}

# ===================== 3. 统计每只股票首次上榜日期 =====================
stock_first_appear = {}
for day in all_days_list:
    dt = day["date"]
    for s in day["stocks"]:
        code = s["code"]
        if code not in stock_first_appear:
            stock_first_appear[code] = dt

total_stock = len(stock_first_appear)
print(f"📊 窗口内涉及个股总数：{total_stock}")

# ===================== 4. 单只股票拉取逻辑 =====================
def task_fetch_stock(code):
    first_dt = stock_first_appear[code]
    prices = cache_price_map.get(code, {})

    # 规则：
    # 只取：首次上榜日期 ～ 窗口结束日期
    # 且只在最近10个交易日窗口内
    need_dates = []
    for d_obj in latest_10_day_objs:
        d = d_obj["date"]
        if d >= first_dt:
            need_dates.append(d)

    # 逐个判断：已有有效价格就跳过，没有才请求
    for dt in need_dates:
        if dt in prices and prices[dt] not in (None, 0, 0.0, ""):
            continue
        try:
            prices[dt] = get_price(code, dt)
        except Exception:
            prices[dt] = 0.0

    return code, prices

# ===================== 5. 多线程并发拉取 =====================
print(f"\n🚀 开始多线程拉取行情...")
final_price_map = {}
with ThreadPoolExecutor(MAX_WORKERS) as exe:
    results = exe.map(task_fetch_stock, stock_first_appear.keys())
    for code, p_map in results:
        final_price_map[code] = p_map

print("✅ 全部行情拉取完成")

# ===================== 6. 按原格式组装新JSON =====================
out_data = {
    "month": raw_data.get("month", ""),
    "days": []
}

# 原样复刻所有天数结构，只给个股追加 price_10d
for day in all_days_list:
    new_day = {
        "date": day["date"],
        "stocks": []
    }
    for s in day["stocks"]:
        new_stock = s.copy()
        # 只回填我们窗口内计算好的价格区间
        new_stock["price_10d"] = final_price_map.get(s["code"], {})
        new_day["stocks"].append(new_stock)
    out_data["days"].append(new_day)

# ===================== 7. 保存文件 =====================
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(out_data, f, ensure_ascii=False, indent=2)

print(f"\n✅ 任务结束！已输出：{OUTPUT_FILE}")
print(f"📌 严格遵循：只取你文件里最后10个交易日窗口")
print(f"📌 每只个股只从自身上榜日往后取，不做空日期请求")
