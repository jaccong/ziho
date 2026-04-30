import requests
import json

# ===================== 【测试单日】2026-04-01 =====================
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

# ===================== 1. 抓取涨停连板列表 =====================
print("【1/2】抓取连板数据...")
zhangting_data = {
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

res = requests.post(API_URL, headers=HEADERS, data=zhangting_data, timeout=10)
print("状态码:", res.status_code)
print("返回:", res.text)

# 如果这一步返回空/无data，后面不用测了
try:
    zt = res.json()
except:
    exit("❌ 连板接口解析失败")

if "data" not in zt or not zt["data"]:
    exit("❌ 当日无涨停数据")

print("✅ 成功获取股票列表，数量:", len(zt["data"]))

# ===================== 2. 抓取第一只股票价格 =====================
stock = zt["data"][0]
code = stock["StockID"]
name = stock["StockName"]

print("\n【2/2】抓取价格 =>", code, name)

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
print("价格接口返回:", res2.text)

try:
    pj = res2.json()
    price = round(float(pj["real"]["last_px"]), 2)
    print("✅ 最终价格:", price)
except:
    print("❌ 价格获取失败")
