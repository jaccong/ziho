# ziho 看板（web/）

涨停雷达看板的前端与接口脚本，部署在 serv00：`ziho.ccwu.cc/ban/`。

## 文件

- `index.html` — 看板页面（深色财经风格，ECharts 图表）
- `save.php` — 被 GitHub Actions（daily.yml 最后一步）调用：从 GitHub raw 拉取最新 `all_history.json`，成功后自动触发 `build.php`
- `build.php` — 预计算接口，生成 `api/`：
  - `api/meta.json` — 数据概况
  - `api/days.json` — 每日统计（涨停数/首板/连板/最高连板）
  - `api/latest.json` — 最新一天明细
  - `api/day/{YYYY-MM-DD}.json` — 单日明细（日期切换按需加载）
  - `api/stocks.json` — 个股全历史统计（涨停次数/最高连板/首次/最近）
- `build_api.py` — 同逻辑的 Python 版（本地构建用）

## 数据流

GitHub Actions 每日抓取 → 提交 `all_history.json` → curl `save.php` → 拉取 + 重建 `api/` → 看板展示
