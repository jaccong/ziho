import json
import requests
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

TODAY = str(date.today())

# 🔴 完全保留你原始请求头，一字不动
HEADERS = {
    "Host": "apphwhq.kaipanhong.com",
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "Connection": "keep-alive",
    "Accept": "*/*",
    "User-Agent": "%E5%BC%80%E7%9B%98%E7%BA%A2/9 CFNetwork/1399 Darwin/22.1.0",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

# 接口地址配置
URL_TODAY = "https://apphwhq.kaipanhong.com/w1/api/index.php"
URL_HIST  = "https://apphis.kaipanhong.com/w1/api/index.php"

# ==============================
# 根据日期自动获取涨停列表
# 今日走今日URL+参数，历史走历史URL+Host+DAY参数
# ==============================
def get_zt_by_date(query_date):
    if query_date == TODAY:
        url = URL_TODAY
        host = "apphwhq.kaipanhong.com"
        data = {
            "Date": query_date,
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
    else:
        url = URL_HIST
        host = "apphis.kaipanhong.com"
        data = {
            "Date": query_date,
            "DAY": query_date,
            "DeviceID": "",
            "PhoneOSNew": "2",
            "Red": "1",
            "Token": "",
            "UserID": "",
            "VerSion": "1.0.4",
            "a": "",   # 你自己填历史涨停a
            "apiv": "w45",
            "c": ""    # 你自己填历史涨停c
        }
    # 切换Host，其余Header完全沿用你的原版
    hds = HEADERS.copy()
    hds["Host"] = host
    try:
        res = requests.post(url, headers=hds, data=data, timeout=15)
        return res.json()
    except:
        return None

# ==============================
# 根据日期自动获取股价
# 今日/历史自动切URL、Host、历史带DAY
# ==============================
def get_price_by_date(code, query_date):
    if query_date == TODAY:
        url = URL_TODAY
        host = "apphwhq.kaipanhong.com"
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
    else:
        url = URL_HIST
        host = "apphis.kaipanhong.com"
        data = {
            "DeviceID": "",
            "PhoneOSNew": "2",
            "Red": "1",
            "StockID": code,
            "DAY": query_date,
            "Token": "",
            "UserID": "",
            "VerSion": "1.0.4",
            "a": "",   # 你自己填历史价格a
            "apiv": "w45",
            "c": ""    # 你自己填历史价格c
        }
    hds = HEADERS.copy()
    hds["Host"] = host
    try:
        j = requests.post(url, headers=hds, data=data, timeout=10).json()
        return round(float(j["real"]["last_px"]), 2)
    except:
        return 0.0
