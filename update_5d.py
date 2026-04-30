import json
import datetime
from concurrent.futures import ThreadPoolExecutor

# 这里导入你自己的接口工具
from get_data import get_price

# ===================== 配置 =====================
INPUT_JSON = "all_history.json"
OUTPUT_JSON = "5d_zt_data.json"
LOOKBACK_DAYS = 5
MAX_WORKERS = 10

# ===================== 加载最近5天数据 =====================
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

all_days = data["days"]
recent_days = all_days[-LOOKBACK_DAYS:]
dates = [d["date"] for d in recent_days]

# 收集所有股票代码
codes = set()
for day in recent_days:
    for s in day["stocks"]:
        codes.add(s["code"])
codes = list(codes)

# ===================== 多线程获取每日价格 =====================
price_map = {}

def fetch_price(code):
    res = {}
    for d in dates:
        try:
            res[d] = get_price(code, d)
        except:
            res[d] = 0.0
    return code, res

with ThreadPoolExecutor(MAX_WORKERS) as executor:
    for code, prices in executor.map(fetch_price, codes):
        price_map[code] = prices

# ===================== 组装新 JSON =====================
output = {
    "month": data.get("month"),
    "recent_days": dates,
    "days": []
}

for day in recent_days:
    new_stocks = []
    for s in day["stocks"]:
        code = s["code"]
        new_stocks.append({
            "date": day["date"],
            "code": code,
            "name": s["name"],
            "lianban": s["lianban"],
            "sector": s["sector"],
            "close": s["close"],
            "prices_5d": price_map.get(code, {})
        })
    output["days"].append({
        "date": day["date"],
        "stocks": new_stocks
    })

# ===================== 保存 =====================
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✅ 完成！已生成 {OUTPUT_JSON}")
print(f"📅 日期：{dates}")
print(f"📊 股票数量：{len(codes)}")
