import json
from datetime import datetime

# ===================== 配置 =====================
INPUT_FILE = "10days_data.json"

# 策略A：首板回调（高收益）
STRATEGY_A = {
    "name": "首板回调买入",
    "lianban": 1,
    "回调区间": (-8, -3),
    "止盈": 12,
    "止损": -6,
    "持有天数": 3
}

# 策略B：二板回调（最稳健）
STRATEGY_B = {
    "name": "二板回调买入",
    "lianban": 2,
    "回调区间": (-6, -2),
    "止盈": 10,
    "止损": -5,
    "持有天数": 3
}

# ===================== 加载数据 =====================
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)
all_days = data["days"]

# ===================== 详细回测函数 =====================
def backtest_detail(strategy):
    name = strategy["name"]
    target_lb = strategy["lianban"]
    low_cb, high_cb = strategy["回调区间"]
    take_profit = strategy["止盈"]
    stop_loss = strategy["止损"]
    max_hold = strategy["持有天数"]

    trades = []
    done = set()

    print("\n" + "="*110)
    print(f"📊 策略：{name}")
    print(f"规则：{target_lb}板 | 回调{low_cb}% ~ {high_cb}% | 止盈{take_profit}% | 止损{stop_loss}% | 最长持有{max_hold}天")
    print("="*110)
    print(f"{'序号':<4}{'代码':<8}{'名称':<10}{'首板日期':<12}{'入场价':<8}{'最高收益':<10}{'最终收益':<10}{'结果':<8}{'持有天数'}")
    print("-"*110)

    idx = 0
    for day in all_days:
        date = day["date"]
        for stock in day["stocks"]:
            code = stock["code"]
            name = stock["name"]
            lb = stock.get("lianban", 0)
            p10d = stock.get("price_10d", {})

            if lb != target_lb:
                continue
            if code in done:
                continue
            done.add(code)

            # 按时间排序
            dt_list = sorted(p10d.keys())
            price_list = [p10d[d] for d in dt_list if p10d[d] not in (0, 0.0, None)]
            if len(price_list) < 2:
                continue

            entry = price_list[0]
            profit_list = []
            for i in range(1, min(max_hold + 1, len(price_list))):
                p = price_list[i]
                profit = (p - entry) / entry * 100
                profit_list.append(round(profit, 2))

            if not profit_list:
                continue

            max_p = max(profit_list) if profit_list else 0
            min_p = min(profit_list) if profit_list else 0
            hit_take = max_p >= take_profit
            hit_stop = min_p <= stop_loss
            final_p = profit_list[-1]
            hold_days = len(profit_list)

            if hit_take:
                res = "止盈"
                final = take_profit
            elif hit_stop:
                res = "止损"
                final = stop_loss
            else:
                res = "持有"
                final = final_p

            idx += 1
            mark = "🟢" if final > 0 else "🔴"
            print(f"{idx:<4}{code:<8}{name:<10}{date:<12}{entry:<8.2f}{max_p:<10.2f}{final:<10.2f}{res:<8}{hold_days}")

            trades.append({
                "code": code,
                "name": name,
                "date": date,
                "entry": entry,
                "max": max_p,
                "final": final,
                "result": res,
                "hold": hold_days
            })

    # 统计
    total = len(trades)
    win = len([t for t in trades if t["final"] > 0])
    loss = len([t for t in trades if t["final"] < 0])
    win_rate = win / total * 100 if total else 0
    total_profit = sum(t["final"] for t in trades)
    avg_profit = total_profit / total if total else 0

    print("-"*110)
    print(f"汇总：总交易{total} | 盈利{win} | 亏损{loss} | 胜率{win_rate:.1f}% | 总收益{total_profit:.1f}% | 平均收益{avg_profit:.1f}%")
    print("="*110)

# ===================== 执行 =====================
backtest_detail(STRATEGY_A)
backtest_detail(STRATEGY_B)
