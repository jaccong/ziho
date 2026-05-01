import json
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入你刚才的get_data.py
from get_data import get_zt_list, get_price, error_stock_list, print_error_report

TODAY = str(date.today())
MAX_WORKERS = 10

if __name__ == "__main__":
    print(f"📅 今日日期：{TODAY}")
    
    # 调用get_data.py 获取涨停列表
    zt_data = get_zt_list(TODAY)
    
    # 关键校验：空值、无效值、无StockList 直接终止，不入库
    if not zt_data or not isinstance(zt_data, dict) or "StockList" not in zt_data or not zt_data["StockList"]:
        print("❌ 涨停数据为空/无效，跳过今日数据入库")
        exit()

    stock_list = zt_data["StockList"]
    print(f"✅ 今日涨停数：{len(stock_list)}")

    # 多线程调用get_data.py的get_price
    price_map = {}
    with ThreadPoolExecutor(MAX_WORKERS) as exe:
        task_map = {exe.submit(get_price, s[0], TODAY): s[0] for s in stock_list}
        for fut in as_completed(task_map):
            price_map[task_map[fut]] = fut.result()

    # 构造结果结构
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

    # 读取历史库
    try:
        with open("all_history.json", "r", encoding="utf-8") as f:
            history = json.load(f)
    except:
        history = {"days": []}

    # 去重追加
    dates = [d["date"] for d in history["days"]]
    if TODAY not in dates:
        history["days"].append(result)
        history["days"].sort(key=lambda x: x["date"])

    # 写入历史库
    with open("all_history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print("✅ 今日数据 + 历史总库 更新完成")
    
    # 打印价格获取失败的错误报告
    print_error_report()
