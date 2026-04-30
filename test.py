import requests
import json

# 测试日期（改成你要测的）
day = "2026-04-01"

API_URL = "https://apphis.kaipanhong.com/w1/api/index.php"

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "User-Agent": "Kaipanhong/9 CFNetwork/1399 Darwin/22.1.0",
    "Accept": "*/*",
}

data = {
    "Day": day,
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

print("测试日期:", day)
print("发送请求...")

res = requests.post(API_URL, headers=HEADERS, data=data, timeout=10)

print("状态码:", res.status_code)
print("响应长度:", len(res.text))
print("完整响应:", res.text)
