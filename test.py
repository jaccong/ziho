import json

# ===================== 配置 =====================
INPUT_FILE = "10days_data.json"

# 策略A：首板回调（你最初要的版本）
STRATEGY_A = {
    "name": "首板 → 3天内回调 -3% ~ -8% 买入",
    "lianban": 1,
    "check_days": 3,      # 首板后 3天内出现回调才买
    "call_back": (-8, -3), # 回调区间
    "hold_max": 3,        # 买入后最多持3天
    "take": 12,           # 止盈12%
    "stop": -6            # 止损-6%
}

# 策略B：二板回调（你最初要的版本）
STRATEGY_B = {
    "name": "二板 → 3天内回调 -2% ~ -6% 买入",
    "lianban": 2,
    "check_days": 3,
    "call_back": (-6, -2),
    "hold_max": 3,
    "take": 10,
    "stop": -5
}

# ===================== 加载数据 =====================
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)
all_days = data["days"]

# ===================== 回测引擎 =====================
def backtest(strategy):
    name = strategy["name"]
    target_lb = strategy["lianban"]
    check_days = strategy["check_days"]
    cb_low, cb_high = strategy["call_back"]
    hold_max = strategy["hold_max"]
    take = strategy["take"]
    stop = strategy["stop"]

    trades = []
    processed = set()

    print("\n" + "="*120)
    print(f"📊 策略：{name}")
    print(f"规则：{target_lb}板 → 后{check_days}天内回调{cb_low}%~{cb_high}% → 买入 → 止盈{take}%/止损{stop}%/持{hold_max}天")
    print("="*120)
    print(f"{'序号':<3}{'代码':<8}{'名称':<10}{'涨停日':<12}{'买入日':<12}{'买入价':<8}{'最高':<8}{'最低':<8}{'收益%':<8}{'结果'}")
    print("-"*120)

    idx = 0
    for day in all_days:
        for stock in day["stocks"]:
            code = stock["code"]
            s_name = stock["name"]
            lb = stock.get("lianban", 0)
            p10d = stock.get("price_10d", {})

            if lb != target_lb:
                continue
            if code in processed:
                continue

            dt_list = sorted(p10d.keys())
            price_list = [p10d[d] for d in dt_list if p10d[d] not in (0, None, 0.0)]
            zt_price = price_list[0] if len(price_list) >= 1 else 0
            future = price_list[1:]

            if len(future) < 1:
                continue

            # ===== 核心逻辑：N天内出现符合条件的回调才买入 =====
            buy_price = None
            buy_day_idx = None

            for i in range(min(check_days, len(future))):
                p = future[i]
                ret = (p - zt_price) / zt_price * 100
                if cb_low <= ret <= cb_high:
                    buy_price = p
                    buy_day_idx = i
                    break

            if buy_price is None:
                continue

            # 买入后持仓
            hold_prices = future[buy_day_idx : buy_day_idx + hold_max]
            if len(hold_prices) < 1:
                continue

            returns = [(p - buy_price) / buy_price * 100 for p in hold_prices]
            max_r = max(returns)
            min_r = min(returns)
            final_r = returns[-1]

            # 止盈止损
            if max_r >= take:
                res = "止盈"
                final = take
            elif min_r <= stop:
                res = "止损"
                final = stop
            else:
                res = "持有"
                final = final_r

            idx += 1
            processed.add(code)
            mark = "🟢" if final > 0 else "🔴"
            zt_date = dt_list[0]
            buy_date = dt_list[1 + buy_day_idx]

            print(f"{idx:<3}{mark}{code:<8}{s_name:<10}{zt_date:<12}{buy_date:<12}{buy_price:<8.2f}{max_r:<8.1f}{min_r:<8.1f}{final:<8.1f}{res}")

            trades.append({"code":code,"final":final})

    # 统计
    total = len(trades)
    win = len([t for t in trades if t["final"]>0])
    loss = len([t for t in trades if t["final"]<0])
    wr = win/total*100 if total else 0
    total_p = sum(t["final"] for t in trades)
    avg_p = total_p/total if total else 0

    print("-"*120)
    print(f"✅ 总交易:{total} 盈利:{win} 亏损:{loss} 胜率:{wr:.1f}% 总收益:{total_p:.1f}% 平均:{avg_p:.1f}%")
    print("="*120)

# ===================== 执行 =====================
backtest(STRATEGY_A)
backtest(STRATEGY_B)
