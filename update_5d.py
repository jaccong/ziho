import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

API_URL = "https://apphwhq.kaipanhong.com/w1/api/index.php"
MAX_WORKERS = 50

session = requests.Session()

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "Connection": "keep-alive",
    "Accept": "*/*",
    "User-Agent": "开盘红/9 CFNetwork/1399 Darwin/22.1.0",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate",
}

# =========================
# 1️⃣ 读取所有日期
# =========================
def get_all_dates(file="all_history.json"):
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        return []

    dates = [d["date"] for d in data.get("days", []) if "date" in d]
    return sorted(set(dates))


# =========================
# 2️⃣ 获取某一天涨停数据
# =========================
def fetch_daily_zt(date_str):
    data = {
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
        r = session.post(API_URL, headers=HEADERS, data=data, timeout=15)
        return r.json()
    except Exception as e:
        print("zt error:", date_str, e)
        return None


# =========================
# 3️⃣ 获取价格（带并发用）
# =========================
def fetch_price(code):
    data = {
        "StockID": code,
        "DeviceID": "",
        "PhoneOSNew": "2",
        "Red": "1",
        "Token": "",
        "UserID": "",
        "VerSion": "1.0.4",
        "a": "GetStockPanKou_Narrow",
        "apiv": "w45",
        "c": "StockL2Data"
    }

    try:
        r = session.post(API_URL, headers=HEADERS, data=data, timeout=10)
        j = r.json()
        return round(float(j["real"]["last_px"]), 2)
    except:
        return 0.0


# =========================
# 4️⃣ 单日处理
# =========================
def process_day(date_str):
    print(f"\n📅 处理日期：{date_str}")

    zt_data = fetch_daily_zt(date_str)
    if not zt_data or "StockList" not in zt_data:
        print("❌ 无数据:", date_str)
        return None

    stock_list = zt_data["StockList"]
    print(f"✅ 涨停数：{len(stock_list)}")

    price_map = {}

    with ThreadPoolExecutor(MAX_WORKERS) as exe:
        futures = {exe.submit(fetch_price, s[0]): s[0] for s in stock_list}

        for f in as_completed(futures):
            code = futures[f]
            price_map[code] = f.result()

    return {
        "date": date_str,
        "stocks": [
            {
                "code": s[0],
                "name": s[1],
                "lianban": s[2],
                "sector": s[5] if len(s) > 5 else "未知",
                "close": price_map.get(s[0], 0.0)
            }
            for s in stock_list
        ]
    }


# =========================
# 5️⃣ 主流程
# =========================
if __name__ == "__main__":

    dates = get_all_dates()

    if not dates:
        print("❌ 没有日期")
        exit()

    print(f"📊 共 {len(dates)} 个交易日")

    all_results = []

    for d in dates:
        result = process_day(d)
        if result:
            all_results.append(result)

    # =========================
    # 保存结果
    # =========================
    final = {"days": all_results}

    with open("full_result.json", "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print("\n✅ 全部处理完成")
