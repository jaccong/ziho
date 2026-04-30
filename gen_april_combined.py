import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===================== 基础配置 =====================
API_URL = "https://apphiskaipanhongcom/w1/api/indexphp"
YEAR = 2026
MONTH = 4
MAX_WORKERS = 8

# 完整抓包原生Header
HEADERS = {
    "Host": "apphis.kaipanhong.com",
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "Connection": "keep-alive",
    "Accept": "*/*",
    "User-Agent": "%E5%BC%80%E7%9B%98%E7%BA%A2/9 CFNetwork/1399 Darwin/22.1.0",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

stats = {
    "total_days": 0,
    "success_days": 0,
    "empty_days": 0,
    "total_stocks": 0,
    "success_price": 0,
    "fail_price": 0
}

# ===================== 1 连板接口 → 使用 Date =====================
def fetch_zt_list(date_str):
    post_data = {
        "Date": date_str,
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
        resp = requests.post(API_URL, headers=HEADERS, data=post_data, timeout=12)
        return resp.json()
    except Exception as e:
        print(f"[ERR] 连板请求异常: {e}")
        return None

# ===================== 2 价格接口 → 使用 Day =====================
def fetch_stock_price(day_str, code):
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
        resp = requests.post(API_URL, headers=HEADERS, data=post_data, timeout=8)
        js = resp.json()
        price = round(float(js["real"]["last_px"]), 2)
        return price, True
    except:
        return 0.0, False

# ===================== 3 单日处理逻辑 =====================
def process_single_day(date_str):
    print(f"\n📅 正在处理: {date_str}")
    zt_json = fetch_zt_list(date_str)

    # 校验正确字段 StockList
    if not zt_json or "StockList" not in zt_json:
        print(f"   ⚪ 无有效连板数据")
        stats["empty_days"] += 1
        return None

    stock_raw_list = zt_json["StockList"]
    if not isinstance(stock_raw_list, list) or len(stock_raw_list) == 0:
        print(f"   ⚪ 当日无涨停")
        stats["empty_days"] += 1
        return None

    stock_count = len(stock_raw_list)
    stats["total_stocks"] += stock_count
    print(f"   ✅ 抓到股票数量: {stock_count}")

    # 多线程批量拿价格
    price_map = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as exe:
        tasks = {}
        for item in stock_raw_list:
            code = item[0]
            tasks[exe.submit(fetch_stock_price, date_str, code)] = code

        for future in as_completed(tasks):
            code = tasks[future]
            price, ok = future.result()
            price_map[code] = price
            if ok:
                stats["success_price"] += 1
            else:
                stats["fail_price"] += 1

    # 组装结构化数据
    day_body = {
        "date": date_str,
        "stocks": []
    }

    for item in stock_raw_list:
        day_body["stocks"].append({
            "code": item[0],
            "name": item[1],
            "lianban": item[3],
            "sector": item[5] if len(item)>=6 else "未知",
            "close": price_map.get(item[0], 0.0)
        })

    stats["success_days"] += 1
    return day_body

# ===================== 4 生成4月全部日期 =====================
def get_april_full_days():
    days = []
    for d in range(1, 31):
        days.append(f"{YEAR}-{MONTH:02d}-{d:02d}")
    return days

# ===================== 主入口 =====================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 2026年04月 连板+收盘价 全量抓取启动")
    print("=" * 60)

    all_days = get_april_full_days()
    stats["total_days"] = len(all_days)
    final_days_data = []

    for d in all_days:
        res = process_single_day(d)
        if res:
            final_days_data.append(res)

    # 按日期升序排序
    final_days_data.sort(key=lambda x: x["date"])

    # 写出最终JSON
    output = {
        "month": "2026年04月",
        "days": final_days_data
    }
    with open("april_combined.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 汇总报告
    print("\n" + "=" * 60)
    print("📋 抓取完成汇总报告")
    print("=" * 60)
    print(f"总遍历日期: {stats['total_days']}")
    print(f"有效数据天数: {stats['success_days']}")
    print(f"空/无数据天数: {stats['empty_days']}")
    print(f"累计股票总数: {stats['total_stocks']}")
    print(f"价格获取成功: {stats['success_price']}")
    print(f"价格获取失败: {stats['fail_price']}")
    print("=" * 60)
    print("✅ 文件已保存: april_combined.json")
