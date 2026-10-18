#!/usr/bin/env python3
"""ziho 接口预计算：从 all_history.json 生成 api/*.json（供前端看板使用）"""
import json, os
from collections import defaultdict

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "all_history.json")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api")

def main():
    with open(SRC, encoding="utf-8") as f:
        raw = json.load(f)
    days = sorted(raw["days"], key=lambda d: d["date"])
    os.makedirs(OUT, exist_ok=True)

    # ---- days.json: 每日摘要 ----
    day_list = []
    for d in days:
        sts = d["stocks"]
        lb_dist = defaultdict(int)
        shouban = lianban_n = 0
        max_lb = 0
        for s in sts:
            lb = s["lianban"]
            lb_dist[str(lb)] += 1
            max_lb = max(max_lb, lb)
            if lb <= 1:
                shouban += 1
            else:
                lianban_n += 1
        day_list.append({
            "date": d["date"],
            "total": len(sts),
            "shouban": shouban,
            "lianban": lianban_n,
            "max_lb": max_lb,
            "lb_dist": dict(lb_dist),
        })

    # ---- stocks.json: 个股全历史统计 ----
    cnt = defaultdict(int); maxlb = defaultdict(int)
    first = {}; last = {}; secs = defaultdict(set); names = {}
    for d in days:
        for s in d["stocks"]:
            c = s["code"]
            cnt[c] += 1
            names[c] = s["name"]
            maxlb[c] = max(maxlb[c], s["lianban"])
            first.setdefault(c, d["date"])
            last[c] = d["date"]
            secs[c].add(s.get("sector", "未知"))
    stocks = [{
        "code": c,
        "name": names[c],
        "count": cnt[c],
        "max_lb": maxlb[c],
        "first": first[c],
        "last": last[c],
        "sectors": sorted(secs[c]),
    } for c in cnt]
    stocks.sort(key=lambda x: (-x["count"], -x["max_lb"]))

    # ---- latest.json: 最新一天 ----
    latest_day = days[-1]
    summary = day_list[-1]
    # 当日板块分布 top
    sec_cnt = defaultdict(int)
    for s in latest_day["stocks"]:
        sec_cnt[s.get("sector", "未知")] += 1
    sectors_top = sorted(sec_cnt.items(), key=lambda x: -x[1])[:15]
    latest = {
        "date": latest_day["date"],
        "summary": summary,
        "sectors_top": [{"sector": k, "count": v} for k, v in sectors_top],
        "stocks": latest_day["stocks"],
    }

    # ---- meta.json ----
    meta = {
        "updated_at": latest_day["date"],
        "total_days": len(days),
        "date_range": [days[0]["date"], days[-1]["date"]],
        "total_stocks": len(stocks),
    }

    for name, obj in [("days.json", day_list), ("stocks.json", stocks),
                      ("latest.json", latest), ("meta.json", meta)]:
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        print(name, os.path.getsize(os.path.join(OUT, name)), "bytes")

    # ---- day/{date}.json: 单日明细（日期切换按需加载） ----
    day_dir = os.path.join(OUT, "day")
    os.makedirs(day_dir, exist_ok=True)
    summaries = {d["date"]: d for d in day_list}
    for d in days:
        one = {"date": d["date"], "summary": summaries[d["date"]], "stocks": d["stocks"]}
        p = os.path.join(day_dir, d["date"] + ".json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(one, f, ensure_ascii=False, separators=(",", ":"))
    print(f"day/*.json {len(days)} files")

if __name__ == "__main__":
    main()
