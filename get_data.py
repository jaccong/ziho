import json
import requests
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

TODAY = str(date.today())

# ========= 完全原样保留你的请求头，一字不改 =========
BASE_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "Connection": "keep-alive",
    "Accept": "*/*",
    "User-Agent": "%E5%BC%80%E7%9B%98%E7%BA%A2/9 CFNetwork/1399 Darwin/22.1.0",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

# 接口配置
URL_TODAY = "https://apphwhq.kaipanhong.com/w1/api/index.php"
HOST_TODAY = "apphwhq.kaipanhong.com"

URL_HIST  = "https://apphis.kaipanhong.com/w1/api/index.php"
HOST_HIST  = "apphis.kaipanhong.com"

# ==============================
# 获取涨停列表：传日期自动判断
# ==============================
def get_zt_list(query_date):
    if query_date == TODAY:
        url = URL_TODAY
        host = HOST_TODAY
        data = {
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
        host = HOST_HIST
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

    # 仅复制基础头，只改Host，其他全部原样
    headers = BASE_HEADERS.copy()
    headers["Host"] = host

    try:
        res = requests.post(url, headers=headers, data=data, timeout=15)
        return res.json()
    except:
        return None

# ==============================
# 获取个股价格：传日期自动判断
# ==============================
def get_price(code, query_date):
    if query_date == TODAY:
        url = URL_TODAY
        host = HOST_TODAY
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
    else:
        url = URL_HIST
        host = HOST_HIST
        data = {
            "StockID": code,
            "DAY": query_date,
            "DeviceID": "",
            "PhoneOSNew": "2",
            "Red": "1",
            "Token": "",
            "UserID": "",
            "VerSion": "1.0.4",
            "a": "GetStockPanKou", 
            "apiv": "w45",
            "c": "StockL2History"   
        }

    # 只动态替换Host，其余Header、UA完全不动
    headers = BASE_HEADERS.copy()
    headers["Host"] = host

    try:
        j = requests.post(url, headers=headers, data=data, timeout=10).json()
        return round(float(j["real"]["last_px"]), 2)
    except:
        return 0.0
