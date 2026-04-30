import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ===================== 固定配置 =====================
API_URL = "https://apphis.kaipanhong.com/w1/api/index.php"
YEAR = 2026
MONTH = 4
MAX_WORKERS = 10

# 🔥 修复：去掉中文，解决编码报错！
HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "User-Agent": "Kaipanhong/9 CFNetwork/1399 Darwin/22.1.0",
    "Accept": "*/*",
}

# ===================== 统计 =====================
stats = {
    "total_days": 0,
    "success_days": 0,
    "fail_days": 0,
    "total_stocks": 0,
    "success_price": 0,
    "fail_price": 0
}

# ===================== 抓取连板数据 =====================
def fetch_zt_data(day_str):
    print(f"\n[DEBUG] 抓取连板 | 日期: {day_str}")

    post_data = {
        "Day": day_str,
        "DeviceID": "",
        "PhoneOSNew": "2",
        "Red": "1",
        "StockID": "",
        "Token": "",
        "UserID": "",
        "VerSion": "1.0.4",
        "a": "GetZTList",
        "apiv": "w45",
        "c": "Stock"
    }

    try:
        response = requests.post(
            API_URL,
            headers=HEADERS,
            data=post_data,
            timeout=15
        )

        print(f"[DEBUG] 状态码: {response.status_code}")
        print(f"[DEBUG] 响应前500字符: {response.text[:500]}")

        if response.status_code != 200:
            return None

        return response.json()

    except Exception as e:
        print(f"[ERROR] 抓取失败: {str(e)}")
        return None

# ===================== 抓取价格 =====================
def fetch_price(day_str, code, name):
    post_data = {
        "Day": day_str,
        "DeviceID": "",
        "PhoneOSNew": "2",
        "Red": "1",
        "StockID": code,
        "Token": "",
        "UserID": "",
        "VerSion": "1.0.4",
        "a": "GetStockPanKou",
        "apiv": "w45",
        "c": "StockL2History"
    }

    try:
        r = requests.post(API_URL, headers=HEADERS, data=post_data, timeout=10)
        j = r.json()
        price = round(float(j.get("real", {}).get("last_px", 0)), 2)
        return code, name, price, True
    except Exception as e:
        return code, name, 0.0, False

# ===================== 处理单日 =====================
def process_day(day_str):
    print(f"\n==================================================")
    print(f"📅 处理日期: {day_str}")
    print(f"==================================================")

    zt = fetch_zt_data(day_str)

    if not zt:
        print(f"❌ 连板数据为空")
        stats["fail_days"] += 1
        return None

    if "StockList" not in zt:
        print(f"❌ 返回数据无 StockList")
        stats["fail_days"] += 1
        return None

    stock_list = zt["StockList"]
    if len(stock_list) == 0:
        print(f"⏭️ 无涨停股票")
        stats["fail_days"] += 1
        return None

    total = len(stock_list)
    stats["total_stocks"] += total
    print(f"\n✅ 获取股票数量: {total}")

    # 多线程获取价格
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

    # 合并数据
    day_result = {"date": day_str, "stocks": []}
    for item in stock_list:
        code = item[0]
        name = item[1]
        lianban = item[3] if len(item) >=4 else 0
        sector = item[5] if len(item) >=6 else "未知"
        close = price_map.get(code, 0.0)

        day_result["stocks"].append({
            "code": code,
            "name": name,
            "lianban": lianban,
            "sector": sector,
            "close": close
        })

    stats["success_days"] += 1
    print(f"\n✅ {day_str} 处理完成")
    return day_result

# ===================== 日期列表 =====================
def get_april_days():
    return [f"{YEAR}-{MONTH:02d}-{d:02d}" for d in range(1, 31)]

# ===================== 主程序 =====================
if __name__ == "__main__":
    print("==================================================")
    print("🚀 4月连板+价格 全自动抓取（已修复编码错误）")
    print("==================================================")

    days = get_april_days()
    stats["total_days"] = len(days)
    print(f"🗓️ 总日期: {len(days)}")

    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_day = {executor.submit(process_day, day): day for day in days}
        for fut in as_completed(future_to_day):
            res = fut.result()
            if res:
                results.append(res)

    # 排序
    results = sorted(results, key=lambda x: x["date"])

    # 生成最终JSON
    final_data = {
        "month": "2026年04月",
        "days": results
    }

    with open("april_combined.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    # 报告
    print("\n\n==================================================")
    print("📋 执行完成报告")
    print("==================================================")
    print(f"总日期: {stats['total_days']}")
    print(f"成功日期: {stats['success_days']}")
    print(f"失败/空日期: {stats['fail_days']}")
    print(f"总股票数: {stats['total_stocks']}")
    print(f"价格成功: {stats['success_price']}")
    print(f"价格失败: {stats['fail_price']}")
    print("==================================================")
    print("✅ 文件已生成: april_combined.json")
