# ZhangJing Stock Tracker

每日股票涨跌追踪器 — 自动获取 A 股今日涨跌幅最大的公司。

## 功能

- ✅ 获取今日涨幅最大的公司（Top Gainers）
- ✅ 获取今日跌幅最大的公司（Top Losers）
- ✅ 支持导出 CSV 报告
- ✅ 支持自定义显示数量
- ✅ 数据来源：东方财富（实时）

## 环境

- Python 3.10+
- 依赖：`requests`, `pandas`, `python-dotenv`

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
# 查看今日涨跌榜（默认每榜10条）
python main.py

# 查看每榜前20名
python main.py --top 20

# 只看涨幅榜
python main.py --gainers-only

# 只看跌幅榜
python main.py --losers-only

# 导出 CSV 报告
python main.py --export csv
```
