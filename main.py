"""
每日股票涨跌追踪器
ZhangJing Stock Tracker

获取A股今日涨跌幅最大的公司
数据来源：东方财富
"""

import sys
import io
import requests
import pandas as pd
import argparse
import os
from datetime import datetime

# 修复 Windows 控制台 GBK 编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─────────────────────────────────────────
# 配置
# ─────────────────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.eastmoney.com/",
}
BASE_URL = "https://push2.eastmoney.com/api/qt/clist/get"

# A股全市场（包括沪深主板、科创板、创业板、北交所）
MARKET_PARAMS = "m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23,m:0+t:80,m:1+t:80"
FIELDS = "f2,f3,f4,f12,f14,f15,f16,f17,f18,f6"

# ─────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────

def fetch_stock_list(asc: bool = False, top: int = 10) -> pd.DataFrame:
    """
    获取涨跌幅榜单

    Args:
        asc: True 查跌幅榜（从小到大），False 查涨幅榜（从大到小）
        top: 取前 N 名

    Returns:
        DataFrame，列：rank, code, name, price, change_pct, change_amt, high, low, volume, turnover
    """
    params = {
        "pn": 1,
        "pz": top,
        "po": 0 if asc else 1,          # 0=asc, 1=desc（按涨幅排序）
        "np": 1,
        "ut": "bd1d9dd880040a15622376ac75ee7b83",
        "fltt": 2,
        "invt": 2,
        "fid": "f3",                      # 按涨幅排序
        "fs": MARKET_PARAMS,
        "fields": FIELDS,
    }

    response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
    response.raise_for_status()
    data = response.json()

    records = data.get("data", {}).get("diff", [])

    rows = []
    for i, item in enumerate(records, 1):
        rows.append({
            "rank":      i,
            "code":      item.get("f12", "-"),
            "name":      item.get("f14", "-"),
            "price":     item.get("f2", "-"),
            "change_pct": item.get("f3", "-"),   # 涨跌幅 %
            "change_amt": item.get("f4", "-"),   # 涨跌额
            "high":      item.get("f15", "-"),
            "low":       item.get("f16", "-"),
            "volume":    item.get("f6", "-"),    #成交量
        })

    df = pd.DataFrame(rows)

    # 格式化数值
    def fmt_pct(x):
        if x == "-":
            return "-"
        return f"{float(x):.2f}%"

    def fmt_price(x):
        if x == "-":
            return "-"
        return f"{float(x):.2f}"

    def fmt_vol(x):
        if x == "-":
            return "-"
        v = float(x)
        if v >= 1e8:
            return f"{v/1e8:.2f}亿"
        elif v >= 1e4:
            return f"{v/1e4:.2f}万"
        return str(int(v))

    df["change_pct"] = df["change_pct"].apply(fmt_pct)
    df["price"]      = df["price"].apply(fmt_price)
    df["high"]       = df["high"].apply(fmt_price)
    df["low"]        = df["low"].apply(fmt_price)
    df["volume"]     = df["volume"].apply(fmt_vol)

    return df


def print_table(title: str, df: pd.DataFrame):
    """打印美化的表格"""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    separator = "═" * 78
    print(f"\n{separator}")
    print(f"  📊 {title}  ({today})")
    print(separator)

    # 涨跌用颜色区分（文字版）
    def colored_pct(pct):
        if pct == "-":
            return pct
        val = float(pct.rstrip("%"))
        if val > 0:
            return f"🔴 +{val:.2f}%"     # 红色 = 涨
        elif val < 0:
            return f"🟢 {val:.2f}%"     # 绿色 = 跌
        return f"  {val:.2f}%"

    header = f"{'排名':<4} {'代码':<10} {'名称':<12} {'现价':>8} {'涨跌幅':>12} {'最高':>8} {'最低':>8}"
    print(header)
    print("─" * 78)

    for _, row in df.iterrows():
        colored = colored_pct(row["change_pct"])
        line = (
            f"{row['rank']:<4} "
            f"{row['code']:<10} "
            f"{row['name']:<12} "
            f"{row['price']:>8} "
            f"{colored:>12} "
            f"{row['high']:>8} "
            f"{row['low']:>8}"
        )
        print(line)
    print(separator)


def export_csv(gainers: pd.DataFrame, losers: pd.DataFrame, filepath: str):
    """导出涨跌榜到 CSV"""
    gainers_out = gainers.copy()
    gainers_out["类型"] = "涨幅榜"
    losers_out = losers.copy()
    losers_out["类型"] = "跌幅榜"

    combined = pd.concat([gainers_out, losers_out], ignore_index=True)
    combined.to_csv(filepath, index=False, encoding="utf-8-sig")
    print(f"\n✅ CSV 已保存: {os.path.abspath(filepath)}")


# ─────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="每日股票涨跌追踪器")
    parser.add_argument("--top",    type=int, default=10, help="每榜显示数量（默认 10）")
    parser.add_argument("--export", choices=["csv"], help="导出数据")
    parser.add_argument("--gainers-only", action="store_true", help="只看涨幅榜")
    parser.add_argument("--losers-only",  action="store_true", help="只看跌幅榜")
    args = parser.parse_args()

    try:
        print("\n🔍 正在获取数据，请稍候...")

        # 获取涨幅榜
        gainers = None
        if not args.losers_only:
            gainers = fetch_stock_list(asc=False, top=args.top)
            print_table("📈 今日涨幅榜 TOP", gainers)

        # 获取跌幅榜
        losers = None
        if not args.gainers_only:
            losers = fetch_stock_list(asc=True, top=args.top)
            print_table("📉 今日跌幅榜 TOP", losers)

        # 导出
        if args.export == "csv":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename  = f"stock_tracker_{timestamp}.csv"
            if gainers is not None and losers is not None:
                export_csv(gainers, losers, filename)
            elif gainers is not None:
                gainers.to_csv(filename, index=False, encoding="utf-8-sig")
            elif losers is not None:
                losers.to_csv(filename, index=False, encoding="utf-8-sig")

    except requests.RequestException as e:
        print(f"\n❌ 网络请求失败: {e}")
    except Exception as e:
        print(f"\n❌ 出错: {e}")


if __name__ == "__main__":
    main()
