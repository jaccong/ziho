import requests
import json

# 日期
date_str = "2026-04-01"
API_URL = "https://apphis.kaipanhong.com/w1/api/index.php"

# 完整请求头
HEADERS = {
    "Host": "apphis.kaipanhong.com",
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "Connection": "keep-alive",
    "Accept": "*/*",
    "User-Agent": "%E5%BC%80%E7%9B%98%E7%BA%A2/9 CFNetwork/1399 Darwin/22.1.0",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

# ===================== 1. 抓取连板数据 =====================
print("【1/2】抓取连板数据...")

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

res = requests.post(API_URL, headers=HEADERS, data=post_data, timeout=10)
data = res.json()

# ✅ 正确字段：StockList
if "StockList" not in data or len(data["StockList"]) == 0:
    exit("❌ 无股票数据")

stock_list = data["StockList"]
print(f"✅ 成功获取 {len(stock_list)} 只涨停股票！")

# ===================== 2. 抓取第一只股票价格 =====================
stock = stock_list[0]
code = stock[0]     # 股票代码
name = stock[1]    # 股票名称

print(f"\n【2/2】抓取价格：{code} {name}")

price_data = {
    "Day": date_str,
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

res2 = requests.post(API_URL, headers=HEADERS, data=price_data, timeout=10)
pj = res2.json()

price = round(float(pj["real"]["last_px"]), 2)
print(f"✅ 成功！价格：{price}")

# ===================== 3. 输出合并结果 =====================
final = {
    "date": date_str,
    "stocks": [
        {
            "code": code,
            "name": name,
            "close": price
        }
    ]
}

print("\n【最终输出】")
print(json.dumps(final, ensure_ascii=False, indent=2))
