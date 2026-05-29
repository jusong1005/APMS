"""
气象数据采集脚本
数据来源：Open-Meteo Historical Weather API（免费、无需API Key）
获取指定地区的历史天气数据，包含日均气温、最高/最低气温、降雨量、湿度等

使用方法：
    pip install requests pandas
    python fetch_weather_data.py
"""

import requests
import pandas as pd
from datetime import datetime
import os
import time

# ============ 配置区域 ============

# 采集的地区及其经纬度
# 选择中国两个农业主产区
REGIONS = {
    "北京": {"latitude": 39.9042, "longitude": 116.4074},
    "山东": {"latitude": 36.6683, "longitude": 116.9972},  # 济南代表山东
}

# 时间范围（近两年数据：2024.01 ~ 2025.04）
START_DATE = "2024-01-01"
END_DATE = "2025-04-30"

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "raw")

# ============ 主逻辑 ============


def fetch_weather_for_region(region_name: str, latitude: float, longitude: float,
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

    print(f"  正在请求 {region_name} 的气象数据...")
    response = requests.get(url, params=params, timeout=30)

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


def weather_code_to_condition(code) -> str:
    """将 WMO 天气代码转换为中文天气描述"""
    if pd.isna(code):
        return "未知"
    code = int(code)
    mapping = {
        0: "晴天",
        1: "大部晴朗", 2: "局部多云", 3: "多云",
        45: "雾", 48: "雾凇",
        51: "小毛毛雨", 53: "中毛毛雨", 55: "大毛毛雨",
        61: "小雨", 63: "中雨", 65: "大雨",
        66: "冻雨(小)", 67: "冻雨(大)",
        71: "小雪", 73: "中雪", 75: "大雪",
        77: "雪粒",
        80: "阵雨(小)", 81: "阵雨(中)", 82: "阵雨(大)",
        85: "阵雪(小)", 86: "阵雪(大)",
        95: "雷暴", 96: "雷暴伴冰雹(小)", 99: "雷暴伴冰雹(大)",
    }
    return mapping.get(code, f"其他({code})")


def main():
    print("=" * 60)
    print("气象数据采集脚本")
    print(f"数据来源: Open-Meteo Historical Weather API")
    print(f"采集时间范围: {START_DATE} ~ {END_DATE}")
    print(f"采集地区: {', '.join(REGIONS.keys())}")
    print("=" * 60)

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_data = []

    for region_name, coords in REGIONS.items():
        df = fetch_weather_for_region(
            region_name=region_name,
            latitude=coords["latitude"],
            longitude=coords["longitude"],
            start_date=START_DATE,
            end_date=END_DATE,
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

    # 保存为 CSV
    output_path = os.path.join(OUTPUT_DIR, "weather_data.csv")
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
