import json
from concurrent.futures import ThreadPoolExecutor
from get_data import get_price

# ==================== 配置 ====================
INPUT_FILE = "all_history.json"
TEST_DATE = "2026-04-29"  # 只测这一天
MAX_WORKERS = 10

# ==================== 加载 ====================
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# 找到当天所有股票
codes = set()
for day in data["days"]:
    if day["date"] == TEST_DATE:
        for s in day["stocks"]:
            codes.add(s["code"])
        break

codes = list(codes)
print(f"📅 测试日期：{TEST_DATE}")
print(f"📊 当天股票数：{len(codes)}")
print("="*70)

# ==================== 多线程抓取 ====================
def fetch_one(code):
    try:
        price = get_price(code, TEST_DATE)
        log = f"{code:8} | {TEST_DATE} → {price}"
        if price in (0, 0.0, None):
            log += " 🔴 异常/0"
        print(log)
        return code, price
    except Exception as e:
        print(f"{code:8} | 报错：{str(e)}")
        return code, 0.0

with ThreadPoolExecutor(MAX_WORKERS) as executor:
    executor.map(fetch_one, codes)

print("="*70)
print("✅ 0429 全量价格测试完成")
print("🔍 看上面：凡是标 🔴 的都是获取失败！")
