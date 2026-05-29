"""
北京新发地批发市场真实价格数据采集脚本

数据来源：北京新发地农产品批发市场 (http://www.xinfadi.com.cn/)
接口：公开 JSON API，无需登录认证
数据内容：每日各品种农产品的最低价、最高价、均价、产地信息

采集品种：番茄、玉米、苹果
时间范围：2024-01-01 ~ 2025-04-30（约16个月）
数据特点：100%真实交易数据，每日更新

使用方法：
    pip install requests pandas
    python fetch_xinfadi_data.py

注意：请合理控制请求频率，避免对服务器造成压力
"""

import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta

# ============ 配置区域 ============

# API 地址
API_URL = "http://www.xinfadi.com.cn/getPriceData.html"

# 目标农产品
PRODUCTS = ["番茄", "玉米", "苹果"]

# 时间范围
START_DATE = "2024-01-01"
END_DATE = "2025-04-30"

# 每次请求的时间跨度（天）— 分批请求避免单次数据量过大
BATCH_DAYS = 30

# 每页数据量
PAGE_LIMIT = 200

# 请求间隔（秒）
REQUEST_DELAY = 0.5

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "raw")

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Origin": "http://www.xinfadi.com.cn",
    "Referer": "http://www.xinfadi.com.cn/priceDetail.html",
}

# ============ 主逻辑 ============


def fetch_product_data(product_name: str, start_date: str, end_date: str) -> list:
    """
    获取指定产品在指定时间范围内的所有价格数据
    自动分页获取全部记录
    """
    all_records = []
    current_page = 1

    while True:
        params = {
            "limit": PAGE_LIMIT,
            "current": current_page,
            "pubDateStartTime": start_date,
            "pubDateEndTime": end_date,
            "prodName": product_name,
        }

        try:
            response = requests.post(API_URL, data=params, headers=HEADERS, timeout=20)

            if response.status_code != 200:
                print(f"      ⚠️ HTTP {response.status_code}")
                break

            data = response.json()
            records = data.get("list", [])
            total_count = data.get("count", 0)

            if not records:
                break

            all_records.extend(records)

            # 检查是否还有更多页
            if len(all_records) >= total_count:
                break

            current_page += 1
            time.sleep(REQUEST_DELAY)

        except requests.exceptions.Timeout:
            print(f"      ⚠️ 请求超时，跳过")
            break
        except Exception as e:
            print(f"      ⚠️ 请求异常: {e}")
            break

    return all_records


def fetch_all_data() -> pd.DataFrame:
    """
    分批获取所有产品的价格数据
    """
    all_data = []

    start = datetime.strptime(START_DATE, "%Y-%m-%d")
    end = datetime.strptime(END_DATE, "%Y-%m-%d")

    for product in PRODUCTS:
        print(f"\n  📦 正在采集: {product}")

        # 分批按月请求
        batch_start = start
        product_total = 0

        while batch_start < end:
            batch_end = min(batch_start + timedelta(days=BATCH_DAYS), end)
            start_str = batch_start.strftime("%Y-%m-%d")
            end_str = batch_end.strftime("%Y-%m-%d")

            print(f"    {start_str} ~ {end_str}...", end=" ")

            records = fetch_product_data(product, start_str, end_str)
            print(f"{len(records)} 条")

            all_data.extend(records)
            product_total += len(records)

            batch_start = batch_end + timedelta(days=1)
            time.sleep(REQUEST_DELAY)

        print(f"  ✅ {product} 合计: {product_total} 条")

    if not all_data:
        return pd.DataFrame()

    # 转换为 DataFrame
    df = pd.DataFrame(all_data)
    return df


def transform_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    将原始 API 数据转换为项目标准格式
    注意：新发地数据单位是"斤"，需要转换为"公斤"（×2）
    """
    print("\n  正在转换数据格式...")

    # 精确筛选目标品种（排除"番茄酱"、"玉米油"、"苹果蕉"等衍生品）
    # 只保留品名完全匹配或属于核心品种的记录
    EXACT_PRODUCTS = {"番茄", "玉米", "苹果"}
    # 也接受这些变体（仍属于生鲜农产品）
    ACCEPTED_VARIANTS = {"寒富苹果", "辽宁寒富苹果", "青苹果", "小玉米"}

    valid_products = EXACT_PRODUCTS | ACCEPTED_VARIANTS

    # 筛选
    mask = raw_df["prodName"].isin(valid_products)
    filtered = raw_df[mask].copy()
    print(f"  精确筛选: {len(raw_df)} → {len(filtered)} 条（排除衍生加工品）")

    # 统一品名（变体归类到主品种）
    name_normalize = {
        "番茄": "番茄",
        "玉米": "玉米",
        "小玉米": "玉米",
        "苹果": "苹果",
        "寒富苹果": "苹果",
        "辽宁寒富苹果": "苹果",
        "青苹果": "苹果",
    }

    # 产品类别映射
    category_map = {
        "番茄": "蔬菜类",
        "玉米": "粮食类",
        "苹果": "水果类",
    }

    # 产地到地区的映射
    def parse_region(place):
        """根据产地信息判断地区"""
        if not place or pd.isna(place):
            return "北京"
        place_str = str(place)
        # 包含山东相关标识
        if "鲁" in place_str or "山东" in place_str:
            return "山东"
        return "北京"

    normalized_name = filtered["prodName"].map(name_normalize).fillna(filtered["prodName"])

    result = pd.DataFrame({
        "product_name": normalized_name,
        "product_category": normalized_name.map(category_map).fillna("其他"),
        "market_name": "北京新发地批发市场",
        "region": filtered["place"].apply(parse_region),
        "date": pd.to_datetime(filtered["pubDate"]).dt.strftime("%Y-%m-%d"),
        # 价格从 元/斤 转换为 元/公斤（×2）
        "highest_price": (pd.to_numeric(filtered["highPrice"], errors="coerce") * 2).round(2),
        "lowest_price": (pd.to_numeric(filtered["lowPrice"], errors="coerce") * 2).round(2),
        "average_price": (pd.to_numeric(filtered["avgPrice"], errors="coerce") * 2).round(2),
        "unit": "元/公斤",
    })

    # 清理无效数据
    result = result.dropna(subset=["average_price"])
    result = result[result["average_price"] > 0]

    # 按日期聚合（同一天同一产品可能有多条不同规格的记录，取日均值）
    print("  正在按日期聚合（同品种同日取均值）...")
    aggregated = result.groupby(["product_name", "product_category", "market_name", "region", "date", "unit"]).agg({
        "highest_price": "max",
        "lowest_price": "min",
        "average_price": "mean",
    }).round(2).reset_index()

    aggregated = aggregated.sort_values(["product_name", "date"]).reset_index(drop=True)

    print(f"  ✅ 转换完成: {len(aggregated)} 条（聚合后）")
    return aggregated


def main():
    print("=" * 60)
    print("北京新发地批发市场 — 真实价格数据采集")
    print(f"数据来源: http://www.xinfadi.com.cn/")
    print(f"目标品种: {', '.join(PRODUCTS)}")
    print(f"时间范围: {START_DATE} ~ {END_DATE}")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 第一步：采集数据
    print("\n[1/2] 正在从新发地 API 采集数据...")
    raw_df = fetch_all_data()

    if raw_df.empty:
        print("\n❌ 未获取到数据，请检查网络连接")
        return

    print(f"\n  原始数据总量: {len(raw_df)} 条")

    # 第二步：转换格式
    print("\n[2/2] 转换为标准格式...")
    result = transform_data(raw_df)

    if result.empty:
        print("\n❌ 数据转换失败")
        return

    # 保存
    output_path = os.path.join(OUTPUT_DIR, "price_data.csv")
    result.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"\n{'=' * 60}")
    print(f"✅ 真实数据采集完成！")
    print(f"   总记录数: {len(result)} 条")
    print(f"   农产品种类: {result['product_name'].nunique()} 种 ({', '.join(result['product_name'].unique())})")
    print(f"   地区数量: {result['region'].nunique()} 个 ({', '.join(result['region'].unique())})")
    print(f"   时间范围: {result['date'].min()} ~ {result['date'].max()}")
    print(f"   保存路径: {output_path}")
    print(f"   数据来源: 北京新发地批发市场（100%真实交易数据）")
    print(f"{'=' * 60}")

    # 统计摘要
    print("\n各品种价格统计（元/公斤）:")
    summary = result.groupby(["product_name"])["average_price"].agg(["count", "mean", "min", "max"])
    summary.columns = ["记录数", "均价", "最低", "最高"]
    print(summary.round(2).to_string())

    # 数据预览
    print("\n\n数据预览（前10行）:")
    print(result.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
