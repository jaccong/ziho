import requests

# 测试日期
day = "2026-04-29"

API_URL = "https://apphis.kaipanhong.com/w1/api/index.php"

# ✅ 完整还原你抓包的 HEADER（一字不差）
HEADERS = {
    "Host": "apphis.kaipanhong.com",
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "Connection": "keep-alive",
    "Accept": "*/*",
    "User-Agent": "CFNetwork/1399 Darwin/22.1.0",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

# ✅ 正确连板接口参数（你抓包原版）
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
print("返回数据:", res.text)
