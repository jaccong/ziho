import json
import requests
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

TODAY = str(date.today())
API_URL = "https://apphwhq.kaipanhong.com/w1/api/index.php"
MAX_WORKERS = 10

HEADERS = {
    "Host": "apphwhq.kaipanhong.com",
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "Connection": "keep-alive",
    "Accept": "*/*",
    "User-Agent": "%E5%BC%80%E7%9B%98%E7%BA%A2/9 CFNetwork/1399 Darwin/22.1.0",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

def fetch_daily_zt():
    data = {
        "Date": TODAY,
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
        res = requests.post(API_URL, headers=HEADERS, data=data, timeout=15)
        return res.json()
    except:
        return None

def fetch_price(code):
    data = {
        "DeviceID": "",
        "PhoneOSNew": "2",
        "Red": "1",
        "StockID": code,
        "Token": "",
        "UserID": "",
        "VerSion": "1.0.4",
        "a": "GetStockPanKou_Narrow",
        "apiv": "w45",
        "c": "StockL2Data"
    }
    try:
        j = requests.post(API_URL, headers=HEADERS, data=data, timeout=10).json()
        return round(float(j["real"]["last_px"]), 2)
    except:
        return 0.0

if __name__ == "__main__":
    print(f"📅 今日日期：{TODAY}")
    zt_data = fetch_daily_zt()
    if not zt_data or "StockList" not in zt_data:
        print("❌ 今日非交易日/无涨停数据")
        exit()

    stock_list = zt_data["StockList"]
    print(f"✅ 今日涨停数：{len(stock_list)}")

    price_map = {}
    with ThreadPoolExecutor(MAX_WORKERS) as exe:
        task_map = {exe.submit(fetch_price, s[0]): s[0] for s in stock_list}
        for fut in as_completed(task_map):
            price_map[task_map[fut]] = fut.result()

    result = {
        "date": TODAY,
        "stocks": [
            {
                "code": s[0],
                "name": s[1],
                "lianban": s[2],
                "sector": s[5] if len(s) >= 6 else "未知",
                "close": price_map.get(s[0], 0.0)
            } for s in stock_list
        ]
    }

    with open(f"{TODAY}_zhangting.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    try:
        with open("all_history.json", "r", encoding="utf-8") as f:
            history = json.load(f)
    except:
        history = {"days": []}

    dates = [d["date"] for d in history["days"]]
    if TODAY not in dates:
        history["days"].append(result)
        history["days"].sort(key=lambda x: x["date"])

    with open("all_history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print("✅ 今日数据 + 历史总库 更新完成")
