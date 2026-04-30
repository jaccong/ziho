import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ===================== 配置 =====================
API_URL = "https://apphis.kaipanhong.com/w1/api/index.php"

YEAR = 2026
MONTH = 4
MAX_WORKERS = 15

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "User-Agent": "开盘红/9 CFNetwork/1399 Darwin/22.1.0"
}

OUTPUT_FILE = "april_combined.json"

# 统计
stats = {
    "total_days": 0,
    "success_days": 0,
    "fail_days": 0,
    "total_stocks": 0,
    "success_price": 0,
    "fail_price": 0
}

# ===================== 抓取【连板数据】真实接口 =====================
def fetch_zt_data(day_str):
    post_data = {
        "Day": day_str,
        "DeviceID": "",
        "PhoneOSNew": 2,
        "Red": 1,
        "StockID": "",
        "Token": "",
        "UserID": "",
        "VerSion": "1.0.4",
        "a": "GetZTList",       # 🔥 修复：真实连板接口方法
        "apiv": "w45",
        "c": "Stock"            # 🔥 修复：真实控制器
    }

    try:
        r = requests.post(API_URL, headers=HEADERS, data=post_data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None

# ===================== 抓取单股票价格 =====================
def fetch_price(day_str, code, name):
    data = {
        "Day": day_str,
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
        r = requests.post(API_URL, headers=HEADERS, data=data, timeout=10)
        j = r.json()
        price = round(float(j.get("real", {}).get("last_px", 0)), 2)
        return code, name, price, True
    except:
        return code, name, 0.0, False

# ===================== 处理一天 =====================
def process_day(day_str):
    print(f"\n📅 处理日期: {day_str}")

    # 1. 抓取连板数据
    zt = fetch_zt_data(day_str)
    if not zt or "StockList" not in zt:
        print(f"   ❌ 连板数据抓取失败")
        stats["fail_days"] += 1
        return None

    stock_list = zt["StockList"]
    if len(stock_list) == 0:
        print(f"   ⏭️ 无涨停股票")
        stats["fail_days"] += 1
        return None

    total = len(stock_list)
    stats["total_stocks"] += total
    print(f"   📊 共 {total} 只股票")

    # 2. 多线程获取价格
    futures = []
    with ThreadPoolExecutor(MAX_WORKERS) as exe:
        for item in stock_list:
            code = item[0]
            name = item[1]
            futures.append(exe.submit(fetch_price, day_str, code, name))

    price_map = {}
    for f in as_completed(futures):
        code, name, price, ok = f.result()
        if ok:
            price_map[code] = price
            stats["success_price"] += 1
            print(f"   ✅ {code} {name} → {price:.2f}")
        else:
            price_map[code] = 0.0
            stats["fail_price"] += 1
            print(f"   ❌ {code} {name} → 失败")

    # 3. 合并结构
    day_result = {
        "date": day_str,
        "stocks": []
    }

    for item in stock_list:
        code = item[0]
        name = item[1]
        lianban = item[3]
        sector = item[5] if len(item) >= 6 else "未知"
        close = price_map.get(code, 0.0)

        day_result["stocks"].append({
            "code": code,
            "name": name,
            "lianban": lianban,
            "sector": sector,
            "close": close
        })

    stats["success_days"] += 1
    print(f"   ✅ 完成")
    return day_result

# ===================== 4月所有日期 =====================
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
    print("🚀 4月连板 + 价格 全自动合并生成")
    print("📦 输出文件: april_combined.json")
    print("=" * 60)

    days = get_april_days()
    stats["total_days"] = len(days)
    print(f"🗓️ 总日期数: {len(days)}")

    # 并行处理日期
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_day = {executor.submit(process_day, day): day for day in days}
        for fut in as_completed(future_to_day):
            res = fut.result()
            if res:
                results.append(res)

    # 按日期排序
    results = sorted(results, key=lambda x: x["date"])

    # 保存最终 JSON
    final = {
        "month": "2026年4月",
        "days": results
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    # 报告
    print("\n" + "=" * 60)
    print("📋 执行完成报告")
    print("=" * 60)
    print(f"总日期: {stats['total_days']}")
    print(f"成功日期: {stats['success_days']}")
    print(f"失败/空日期: {stats['fail_days']}")
    print(f"总股票数: {stats['total_stocks']}")
    print(f"价格成功: {stats['success_price']}")
    print(f"价格失败: {stats['fail_price']}")
    print(f"\n✅ 文件已生成: {OUTPUT_FILE}")
