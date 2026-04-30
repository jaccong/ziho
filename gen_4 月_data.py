import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ===================== 配置 =====================
API_BASE = "https://apphis.kaipanhong.com/w1/api/index.php"
SAVE_DIR = "zt_data"
MONTH = 4
YEAR = 2026
MAX_WORKERS = 20  # 多线程

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "User-Agent": "开盘红/9 CFNetwork/1399 Darwin/22.1.0"
}

os.makedirs(SAVE_DIR, exist_ok=True)

# 全局统计
stats = {
    "total_days": 0,
    "processed_days": 0,
    "success_days": 0,
    "skipped_days": 0,
    "total_stocks": 0,
    "success_prices": 0,
    "failed_prices": 0
}

# 获取单股票价格
def fetch_price(day, code, name):
    data = {
        "Day": day,
        "DeviceID": "",
        "PhoneOSNew": 2,
        "Red": 1,
        "StockID": code,
        "Token": "",
        "UserID": "",
        "VerSion": "1.0.4",
        "a": "GetStockPanKou",
        "apiv": "w45",
        "c": "StockL2History"
    }
    try:
        r = requests.post(API_BASE, headers=HEADERS, data=data, timeout=10)
        r.raise_for_status()
        j = r.json()
        price = round(float(j.get("real", {}).get("last_px", 0)), 2)
        return code, name, price, True
    except Exception as e:
        return code, name, 0.00, False

# 处理单日数据
def process_day(day_str):
    day_num = day_str.replace("-", "")
    zt_path = f"{SAVE_DIR}/zt_{day_num}.json"

    print(f"\n📅 开始处理日期：{day_str}")

    # 无文件则跳过
    if not os.path.exists(zt_path):
        print(f"   ⏭️  无连板数据，跳过")
        stats["skipped_days"] += 1
        return

    # 读取连板数据
    try:
        with open(zt_path, "r", encoding="utf-8") as f:
            zt = json.load(f)
    except:
        print(f"   ❌ 读取数据失败")
        return

    stock_list = zt.get("StockList", [])
    if not stock_list:
        print(f"   ⏭️  股票列表为空，跳过")
        stats["skipped_days"] += 1
        return

    total = len(stock_list)
    stats["total_stocks"] += total
    print(f"   📊 当日股票数量：{total} 只")

    # 多线程获取价格
    futures = []
    with ThreadPoolExecutor(MAX_WORKERS) as exe:
        for item in stock_list:
            code = item[0]
            name = item[1]
            futures.append(exe.submit(fetch_price, day_str, code, name))

    # 接收结果
    price_map = {}
    success = 0
    fail = 0

    for fut in as_completed(futures):
        code, name, price, ok = fut.result()
        if ok:
            price_map[code] = price
            success += 1
            stats["success_prices"] += 1
            print(f"   ✅ {code} {name} → {price:.2f}")
        else:
            price_map[code] = 0.00
            fail += 1
            stats["failed_prices"] += 1
            print(f"   ❌ {code} {name} → 抓取失败")

    # 生成价格文件
    output = []
    for item in stock_list:
        code = item[0]
        name = item[1]
        output.append({
            "code": code,
            "name": name,
            "close": price_map.get(code, 0.00)
        })

    out_path = f"{SAVE_DIR}/prices_{day_num}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    stats["processed_days"] += 1
    stats["success_days"] += 1
    print(f"   ✅ 日期 {day_str} 处理完成（成功：{success} 失败：{fail}）")

# 生成4月所有日期
def get_april_days():
    days = []
    for d in range(1, 31):
        try:
            dt = datetime(YEAR, MONTH, d)
            days.append(dt.strftime("%Y-%m-%d"))
        except:
            break
    return days

# ===================== 主程序 =====================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 4月连板数据 + 股票价格 批量生成工具（多线程版）")
    print("=" * 60)

    days = get_april_days()
    stats["total_days"] = len(days)
    print(f"🗓️  4月总天数：{len(days)} 天")
    print(f"📂 数据目录：{SAVE_DIR}")
    print(f"🧵 线程数：{MAX_WORKERS}")
    print("=" * 60)

    # 开始处理
    with ThreadPoolExecutor(5) as exe:
        for day in days:
            exe.submit(process_day, day)

    # 最终报告
    print("\n" + "=" * 60)
    print("📋 【最终执行报告】")
    print("=" * 60)
    print(f"总日期数量：{stats['total_days']} 天")
    print(f"成功处理日期：{stats['success_days']} 天")
    print(f"跳过日期：{stats['skipped_days']} 天")
    print(f"总股票数：{stats['total_stocks']} 只")
    print(f"成功抓取价格：{stats['success_prices']} 只")
    print(f"抓取失败：{stats['failed_prices']} 只")
    print("=" * 60)
    print("✅ 全部任务完成！")
