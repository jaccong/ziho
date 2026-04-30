import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===================== 配置 =====================
API_URL = "https://apphis.kaipanhong.com/w1/api/index.php"
YEAR = 2026
MONTH = 4
MAX_WORKERS = 10

# 完整原生请求头
HEADERS = {
    "Host": "apphis.kaipanhong.com",
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "Connection": "keep-alive",
    "Accept": "*/*",
    "User-Agent": "%E5%BC%80%E7%9B%98%E7%BA%A2/9 CFNetwork/1399 Darwin/22.1.0",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

# 统计
stats = {
    "total_days": 0, "success_days": 0, "empty_days": 0,
    "total_stocks": 0, "success_price": 0, "fail_price": 0
}

# ===================== 抓取连板列表：使用 Date =====================
def fetch_zhangting(date_str):
    post_data = {
        "Date": date_str,  # ✅ 连板用 Date
        "DeviceID": "",
        "PhoneOSNew": "2",
        "Red": "1",
        "Token": "",
        "UserID": "",
        "VerSion": "1.0.4",
        "a": "GetZhangTingTianTi",
        "apiv": "w45",
        "c": "FuPanLa"
    }
    try:
        r = requests.post(API_URL, headers=HEADERS, data=post_data, timeout=10)
        return r.json() if r.text.strip() else None
    except:
        return None

# ===================== 抓取价格：使用 Day =====================
def fetch_price(day_str, code, name):
    post_data = {
        "Day": day_str,  # ✅ 价格用 Day
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
        j = requests.post(API_URL, headers=HEADERS, data=post_data, timeout=8).json()
        price = round(float(j["real"]["last_px"]), 2)
        return code, name, price, True
    except:
        return code, name, 0.0, False

# ===================== 处理单日 =====================
def process_day(date_str):
    print(f"\n📅 处理日期: {date_str}")

    # 1. 抓连板
    zt_data = fetch_zhangting(date_str)
    if not zt_data or "data" not in zt_data:
        print(f"   ⚪ 无数据")
        stats["empty_days"] += 1
        return None

    stock_list = zt_data["data"]
    if not isinstance(stock_list, list) or len(stock_list) == 0:
        print(f"   ⚪ 无涨停")
        stats["empty_days"] += 1
        return None

    total = len(stock_list)
    stats["total_stocks"] += total
    print(f"   ✅ 股票数: {total}")

    # 2. 多线程抓价格
    futures = []
    with ThreadPoolExecutor(MAX_WORKERS) as exe:
        for s in stock_list:
            code = s.get("StockID", "")
            name = s.get("StockName", "")
            if code:
                futures.append(exe.submit(fetch_price, date_str, code, name))

    price_map = {}
    for f in as_completed(futures):
        code, name, price, ok = f.result()
        price_map[code] = price
        if ok:
            stats["success_price"] += 1
            print(f"   ✅ {code} {name} → {price:.2f}")
        else:
            stats["fail_price"] += 1
            print(f"   ❌ {code} {name} → 失败")

    # 3. 合并结果
    day_result = {"date": date_str, "stocks": []}
    for s in stock_list:
        code = s.get("StockID", "")
        name = s.get("StockName", "")
        day_result["stocks"].append({
            "code": code,
            "name": name,
            "lianban": s.get("LianBan", 1),
            "sector": s.get("BlockName", "未知"),
            "close": price_map.get(code, 0.0)
        })

    stats["success_days"] += 1
    return day_result

# ===================== 生成4月日期列表 =====================
def get_month_days():
    return [f"{YEAR}-{MONTH:02d}-{d:02d}" for d in range(1, 31)]

# ===================== 主程序 =====================
if __name__ == "__main__":
    print("🚀 2026年4月 连板+价格 全自动抓取")
    days = get_month_days()
    stats["total_days"] = len(days)
    results = []

    for day in days:
        res = process_day(day)
        if res:
            results.append(res)

    # 保存最终文件
    final = {
        "month": "2026年04月",
        "days": results
    }

    with open("april_combined.json", "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    # 输出报告
    print("\n✅ 抓取完成！")
    print(f"总日期: {stats['total_days']}")
    print(f"成功日期: {stats['success_days']}")
    print(f"空日期: {stats['empty_days']}")
    print(f"总股票: {stats['total_stocks']}")
    print(f"价格成功: {stats['success_price']}")
    print(f"价格失败: {stats['fail_price']}")
    print("\n✅ 文件已生成: april_combined.json")
