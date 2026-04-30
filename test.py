import requests

day = "2026-04-01"
API_URL = "https://apphis.kaipanhong.com/w1/api/index.php"

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "User-Agent": "Kaipanhong/9 CFNetwork/1399 Darwin/22.1.0",
    "Accept": "*/*",
}

# 正确连板接口参数
data = {
    "Day": day,
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

print("测试日期:", day)
res = requests.post(API_URL, headers=HEADERS, data=data, timeout=15)
print("状态码:", res.status_code)
print("响应长度:", len(res.text))
print("完整响应:\n", res.text)
