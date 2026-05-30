"""
气象数据采集脚本
数据来源：Open-Meteo Historical Weather API（免费、无需API Key）
获取全国省级地区的历史天气数据，包含日均气温、最高/最低气温、降雨量、湿度等

使用方法：
    pip install requests pandas
    python fetch_weather_data.py
"""

import argparse
import sys
import requests
import pandas as pd
from datetime import date, timedelta
import os
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from config import RAW_PRICE_CSV, RAW_WEATHER_CSV
from data.scripts.realtime_collector import REGION_COORDS, weather_code_to_condition

# ============ 配置区域 ============

# 采集的地区及其经纬度，复用实时采集脚本中的全国省级坐标
REGIONS = REGION_COORDS

# 兜底时间范围；默认会优先按 price_data.csv 的日期范围自动推断
DEFAULT_START_DATE = "2024-01-01"
DEFAULT_END_DATE = "2025-04-30"
REQUEST_TIMEOUT = 60
RETRY_COUNT = 3
WEATHER_WINDOW_DAYS = 180

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "raw")

# ============ 主逻辑 ============


def iter_date_windows(start_date: str, end_date: str):
    current = date.fromisoformat(start_date)
    final = date.fromisoformat(end_date)

    while current <= final:
        window_end = min(current + timedelta(days=WEATHER_WINDOW_DAYS - 1), final)
        yield current.isoformat(), window_end.isoformat()
        current = window_end + timedelta(days=1)


def fetch_weather_window(region_name: str, latitude: float, longitude: float,
                         start_date: str, end_date: str) -> pd.DataFrame:
    """
    从 Open-Meteo API 获取指定地区的历史天气数据

    参数:
        region_name: 地区名称
        latitude: 纬度
        longitude: 经度
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)

    返回:
        包含天气数据的 DataFrame
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join([
            "temperature_2m_mean",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "relative_humidity_2m_mean",
            "sunshine_duration",
            "weather_code",
        ]),
        "timezone": "Asia/Shanghai",
    }

    print(f"  正在请求 {region_name} 的气象数据 {start_date} ~ {end_date}...")
    response = None
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                break
            print(f"  ⚠️ {region_name} 第 {attempt} 次请求返回状态码: {response.status_code}")
            if attempt < RETRY_COUNT:
                time.sleep(attempt * 2)
        except requests.RequestException as exc:
            print(f"  ⚠️ {region_name} 第 {attempt} 次请求失败: {exc}")
            if attempt < RETRY_COUNT:
                time.sleep(attempt * 2)

    if response is None:
        print(f"  ❌ {region_name} 请求多次失败，已跳过")
        return pd.DataFrame()

    if response.status_code != 200:
        print(f"  ❌ 请求失败，状态码: {response.status_code}")
        print(f"     响应内容: {response.text[:200]}")
        return pd.DataFrame()

    data = response.json()

    if "daily" not in data:
        print(f"  ❌ 响应中无 daily 数据")
        return pd.DataFrame()

    daily = data["daily"]

    df = pd.DataFrame({
        "region": region_name,
        "date": daily["time"],
        "average_temperature": daily["temperature_2m_mean"],
        "highest_temperature": daily["temperature_2m_max"],
        "lowest_temperature": daily["temperature_2m_min"],
        "rainfall": daily["precipitation_sum"],
        "humidity": daily["relative_humidity_2m_mean"],
        "sunshine_duration": daily["sunshine_duration"],
        "weather_code": daily["weather_code"],
    })

    print(f"  ✅ 获取 {region_name} 数据 {len(df)} 条")
    return df


def fetch_weather_for_region(region_name: str, latitude: float, longitude: float,
                             start_date: str, end_date: str) -> pd.DataFrame:
    frames = []
    for window_start, window_end in iter_date_windows(start_date, end_date):
        frame = fetch_weather_window(
            region_name=region_name,
            latitude=latitude,
            longitude=longitude,
            start_date=window_start,
            end_date=window_end,
        )
        if not frame.empty:
            frames.append(frame)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def infer_date_range(start_date: str | None, end_date: str | None) -> tuple[str, str]:
    if start_date and end_date:
        return start_date, end_date

    if RAW_PRICE_CSV.exists():
        price_df = pd.read_csv(RAW_PRICE_CSV, usecols=["date"])
        dates = pd.to_datetime(price_df["date"], errors="coerce").dropna()
        if not dates.empty:
            inferred_start = dates.min().date()
            max_archive_date = date.today() - timedelta(days=1)
            inferred_end = min(dates.max().date(), max_archive_date)
            return (start_date or inferred_start.isoformat(), end_date or inferred_end.isoformat())

    return start_date or DEFAULT_START_DATE, end_date or DEFAULT_END_DATE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="采集全国省级历史气象数据")
    parser.add_argument("--start-date", default=None, help="开始日期 YYYY-MM-DD；默认从 price_data.csv 推断")
    parser.add_argument("--end-date", default=None, help="结束日期 YYYY-MM-DD；默认从 price_data.csv 推断，且不超过昨天")
    parser.add_argument("--regions", nargs="+", default=None, help="指定采集地区；默认采集全部省级地区")
    parser.add_argument("--replace", action="store_true", help="覆盖 weather_data.csv；默认与已有数据合并去重")
    return parser.parse_args()


def main():
    args = parse_args()
    start_date, end_date = infer_date_range(args.start_date, args.end_date)
    selected_regions = {
        region: coords
        for region, coords in REGIONS.items()
        if args.regions is None or region in args.regions
    }

    print("=" * 60)
    print("气象数据采集脚本")
    print("数据来源: Open-Meteo Historical Weather API")
    print(f"采集时间范围: {start_date} ~ {end_date}")
    print(f"采集地区: {', '.join(selected_regions.keys())}")
    print("=" * 60)

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_data = []

    for region_name, coords in selected_regions.items():
        df = fetch_weather_for_region(
            region_name=region_name,
            latitude=coords["latitude"],
            longitude=coords["longitude"],
            start_date=start_date,
            end_date=end_date,
        )
        if not df.empty:
            all_data.append(df)
        time.sleep(1)  # 礼貌性延迟，避免请求过快

    if not all_data:
        print("\n❌ 未获取到任何数据，请检查网络连接")
        return

    # 合并所有地区数据
    result = pd.concat(all_data, ignore_index=True)

    # 转换天气代码为中文描述
    result["weather_condition"] = result["weather_code"].apply(weather_code_to_condition)

    # 日照时长从秒转换为小时
    result["sunshine_duration"] = (result["sunshine_duration"] / 3600).round(2)

    # 删除 weather_code 列（已转换为 weather_condition）
    result.drop(columns=["weather_code"], inplace=True)

    if RAW_WEATHER_CSV.exists() and not args.replace:
        existing = pd.read_csv(RAW_WEATHER_CSV)
        result = pd.concat([existing, result], ignore_index=True)
        result = result.drop_duplicates(subset=["region", "date"], keep="last")
        result = result.sort_values(["date", "region"]).reset_index(drop=True)

    # 保存为 CSV
    output_path = str(RAW_WEATHER_CSV)
    result.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"\n{'=' * 60}")
    print(f"✅ 数据采集完成！")
    print(f"   总记录数: {len(result)} 条")
    print(f"   地区数量: {result['region'].nunique()} 个")
    print(f"   时间范围: {result['date'].min()} ~ {result['date'].max()}")
    print(f"   保存路径: {output_path}")
    print(f"{'=' * 60}")

    # 打印数据预览
    print("\n数据预览（前5行）:")
    print(result.head().to_string(index=False))


if __name__ == "__main__":
    main()
