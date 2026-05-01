import json
import requests
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

TODAY = str(date.today())
# 重试配置
RETRY_TIMES = 3       # 最大重试次数
RETRY_DELAY = 0.3     # 重试间隔秒

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

# 错误股票记录
error_stock_list = []

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

    headers = BASE_HEADERS.copy()
    headers["Host"] = host

    try:
        res = requests.post(url, headers=headers, data=data, timeout=15)
        return res.json()
    except Exception as e:
        print(f"获取涨停列表异常: {query_date}, 错误: {str(e)}")
        return None

# ==============================
# 获取个股价格：带重试 + 价格0判定 + 错误记录
# ==============================
def get_price(code, query_date):
    url = ""
    host = ""
    data = {}

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
            "Day": query_date,
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

    headers = BASE_HEADERS.copy()
    headers["Host"] = host

    price = 0.0
    for retry in range(RETRY_TIMES):
        try:
            resp = requests.post(url, headers=headers, data=data, timeout=10)
            j = resp.json()
            px = float(j["real"]["last_px"])
            price = round(px, 2)
            # 价格正常直接返回
            if price > 0:
                return price
        except Exception as e:
            print(f"【重试{retry+1}/{RETRY_TIMES}】{code} {query_date} 请求异常: {str(e)[:60]}")
        
        # 价格为0且不是最后一次，等待后重试
        if retry < RETRY_TIMES - 1:
            import time
            time.sleep(RETRY_DELAY)

    # 重试完还是0，记入错误列表
    err_msg = f"股票{code} 日期{query_date} 重试{RETRY_TIMES}次仍获取价格为0"
    print(err_msg)
    error_stock_list.append({"code": code, "date": query_date, "price": 0.0})
    return 0.0

# ==============================
# 打印错误报告
# ==============================
def print_error_report():
    if not error_stock_list:
        print("\n✅ 所有股票价格获取正常，无错误记录")
        return
    print("\n==================== 错误报告 ====================")
    for item in error_stock_list:
        print(f"❌ 代码:{item['code']} 日期:{item['date']} 价格异常:0.0")
    print("==================================================\n")
