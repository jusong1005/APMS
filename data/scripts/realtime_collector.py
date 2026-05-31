"""
实时数据采集脚本

数据来源：
- 农业农村部重点农产品市场信息平台：全国价格指数、市场价格分布、电子结算价格
- 北京新发地农产品批发市场公开接口：价格数据
- Open-Meteo Forecast API：近实时气象数据

输出文件：
- data/raw/price_data.csv
- data/raw/weather_data.csv

默认执行一次采集；如果传入 --interval-seconds，则按固定间隔循环采集。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

MOA_BASE_URL = "https://ncpscxx.moa.gov.cn"
MOA_WIDE_MARKET_PRICE_URL = f"{MOA_BASE_URL}/product/common-price-avg/getWideMarketVarietyData"
MOA_MARKET_PRICE_URL = f"{MOA_BASE_URL}/product/piMarketPrice/getMarketDatas"
MOA_VARIETY_TREE_URL = f"{MOA_BASE_URL}/price_portal/sys-user-relation/getVarietiesTree"
XINFADI_API_URL = "http://www.xinfadi.com.cn/getPriceData.html"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

DEFAULT_PRODUCTS = ["番茄", "玉米", "苹果", "大白菜", "白条猪"]
PAGE_LIMIT = 200
REQUEST_TIMEOUT = 20
REQUEST_DELAY_SECONDS = 0.4

MOA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 AgriPulse/1.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": f"{MOA_BASE_URL}/",
}

XINFADI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 AgriPulse/1.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Origin": "http://www.xinfadi.com.cn",
    "Referer": "http://www.xinfadi.com.cn/priceDetail.html",
}

MOA_PRODUCT_VARIETY_CODES = {
    "番茄": "AE04001",
    "玉米": "AA01009",
    "苹果": "AF01001",
    "大白菜": "AE01001",
    "白条猪": "AL01002001",
    "猪肉": "AL01002001",
}

MOA_MARKET_CODES = {
    "无锡朝阳农产品大市场": "3202014",
}

PRODUCT_NORMALIZE = {
    "番茄": "番茄",
    "西红柿": "番茄",
    "樱桃番茄": "番茄",
    "番茄(水果)": "番茄",
    "玉米": "玉米",
    "黄玉米": "玉米",
    "花玉米": "玉米",
    "鲜食玉米": "玉米",
    "小玉米": "玉米",
    "苹果": "苹果",
    "红富士苹果": "苹果",
    "富士苹果": "苹果",
    "寒富苹果": "苹果",
    "辽宁寒富苹果": "苹果",
    "青苹果": "苹果",
    "大白菜": "大白菜",
    "毛白菜": "大白菜",
    "白条猪": "猪肉",
    "猪肉(白条猪)": "猪肉",
}

PRODUCT_CODE_NORMALIZE = {
    "AE04001": "番茄",
    "AE04001001": "番茄",
    "AA01009": "玉米",
    "AE04021": "玉米",
    "AF01001": "苹果",
    "AF01001001": "苹果",
    "AE01001": "大白菜",
    "AL01002001": "猪肉",
}

PRODUCT_ALIAS_HINTS = {
    "番茄": ["番茄", "西红柿"],
    "玉米": ["黄玉米", "花玉米", "鲜食玉米", "玉米"],
    "苹果": ["苹果"],
    "大白菜": ["大白菜", "毛白菜"],
    "猪肉": ["猪肉", "白条猪"],
}

PRODUCT_CATEGORY = {
    "番茄": "蔬菜类",
    "玉米": "粮食类",
    "苹果": "水果类",
    "大白菜": "蔬菜类",
    "猪肉": "肉禽蛋类",
}

REGION_HINTS = {
    "北京": ["北京市", "北京", "京"],
    "天津": ["天津市", "天津", "津"],
    "河北": ["河北省", "河北", "冀"],
    "山西": ["山西省", "山西", "晋"],
    "内蒙古": ["内蒙古自治区", "内蒙古", "蒙"],
    "辽宁": ["辽宁省", "辽宁", "辽"],
    "吉林": ["吉林省", "吉林", "吉"],
    "黑龙江": ["黑龙江省", "黑龙江", "黑"],
    "上海": ["上海市", "上海", "沪"],
    "江苏": ["江苏省", "江苏", "苏"],
    "浙江": ["浙江省", "浙江", "浙"],
    "安徽": ["安徽省", "安徽", "皖"],
    "福建": ["福建省", "福建", "闽"],
    "江西": ["江西省", "江西", "赣"],
    "山东": ["山东省", "山东", "鲁", "寿光"],
    "河南": ["河南省", "河南", "豫"],
    "湖北": ["湖北省", "湖北", "鄂"],
    "湖南": ["湖南省", "湖南", "湘"],
    "广东": ["广东省", "广东", "粤"],
    "广西": ["广西壮族自治区", "广西", "桂"],
    "海南": ["海南省", "海南", "琼"],
    "重庆": ["重庆市", "重庆", "渝"],
    "四川": ["四川省", "四川", "川", "蜀"],
    "贵州": ["贵州省", "贵州", "黔", "贵"],
    "云南": ["云南省", "云南", "滇", "云"],
    "西藏": ["西藏自治区", "西藏", "藏"],
    "陕西": ["陕西省", "陕西", "陕", "秦"],
    "甘肃": ["甘肃省", "甘肃", "甘", "陇"],
    "青海": ["青海省", "青海", "青"],
    "宁夏": ["宁夏回族自治区", "宁夏", "宁"],
    "新疆": ["新疆维吾尔自治区", "新疆", "新"],
}

REGION_COORDS = {
    "北京": {"latitude": 39.9042, "longitude": 116.4074},
    "天津": {"latitude": 39.3434, "longitude": 117.3616},
    "河北": {"latitude": 38.0428, "longitude": 114.5149},
    "山西": {"latitude": 37.8706, "longitude": 112.5489},
    "内蒙古": {"latitude": 40.8426, "longitude": 111.7492},
    "辽宁": {"latitude": 41.8057, "longitude": 123.4315},
    "吉林": {"latitude": 43.8171, "longitude": 125.3235},
    "黑龙江": {"latitude": 45.8038, "longitude": 126.5349},
    "上海": {"latitude": 31.2304, "longitude": 121.4737},
    "江苏": {"latitude": 32.0603, "longitude": 118.7969},
    "浙江": {"latitude": 30.2741, "longitude": 120.1551},
    "安徽": {"latitude": 31.8206, "longitude": 117.2272},
    "福建": {"latitude": 26.0745, "longitude": 119.2965},
    "江西": {"latitude": 28.6829, "longitude": 115.8582},
    "山东": {"latitude": 36.6683, "longitude": 116.9972},
    "河南": {"latitude": 34.7466, "longitude": 113.6254},
    "湖北": {"latitude": 30.5928, "longitude": 114.3055},
    "湖南": {"latitude": 28.2282, "longitude": 112.9388},
    "广东": {"latitude": 23.1291, "longitude": 113.2644},
    "广西": {"latitude": 22.8170, "longitude": 108.3669},
    "海南": {"latitude": 20.0440, "longitude": 110.1999},
    "重庆": {"latitude": 29.5630, "longitude": 106.5516},
    "四川": {"latitude": 30.5728, "longitude": 104.0668},
    "贵州": {"latitude": 26.6470, "longitude": 106.6302},
    "云南": {"latitude": 25.0389, "longitude": 102.7183},
    "西藏": {"latitude": 29.6520, "longitude": 91.1721},
    "陕西": {"latitude": 34.3416, "longitude": 108.9398},
    "甘肃": {"latitude": 36.0611, "longitude": 103.8343},
    "青海": {"latitude": 36.6171, "longitude": 101.7782},
    "宁夏": {"latitude": 38.4872, "longitude": 106.2309},
    "新疆": {"latitude": 43.8256, "longitude": 87.6168},
}


def parse_region(place: object) -> str:
    if pd.isna(place) or not str(place).strip():
        return "北京"
    place_text = str(place)
    for region, hints in REGION_HINTS.items():
        if any(hint in place_text for hint in hints):
            return region
    return "其他"


def normalize_product_name(product_name: object, product_code: object = None) -> str | None:
    if not pd.isna(product_code):
        normalized_by_code = PRODUCT_CODE_NORMALIZE.get(str(product_code).strip())
        if normalized_by_code:
            return normalized_by_code

    if pd.isna(product_name) or not str(product_name).strip():
        return None

    product_text = str(product_name).strip()
    if product_text in PRODUCT_NORMALIZE:
        return PRODUCT_NORMALIZE[product_text]

    for normalized_name, aliases in PRODUCT_ALIAS_HINTS.items():
        if any(alias in product_text for alias in aliases):
            return normalized_name
    return None


def weather_code_to_condition(code: object) -> str:
    if pd.isna(code):
        return "未知"
    code = int(code)
    mapping = {
        0: "晴天",
        1: "大部晴朗",
        2: "局部多云",
        3: "多云",
        45: "雾",
        48: "雾凇",
        51: "小毛毛雨",
        53: "中毛毛雨",
        55: "大毛毛雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        80: "阵雨(小)",
        81: "阵雨(中)",
        82: "阵雨(大)",
        95: "雷暴",
        96: "雷暴伴冰雹(小)",
        99: "雷暴伴冰雹(大)",
    }
    return mapping.get(code, f"其他({code})")


def fetch_xinfadi_page(product_name: str, start_date: str, end_date: str, page: int) -> Dict[str, object]:
    params = {
        "limit": PAGE_LIMIT,
        "current": page,
        "pubDateStartTime": start_date,
        "pubDateEndTime": end_date,
        "prodName": product_name,
    }
    response = requests.post(XINFADI_API_URL, data=params, headers=XINFADI_HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def fetch_moa_wide_market_prices(products: Iterable[str]) -> pd.DataFrame:
    records: List[Dict[str, object]] = []
    for product in products:
        normalized_product = normalize_product_name(product) or product
        variety_code = MOA_PRODUCT_VARIETY_CODES.get(normalized_product) or MOA_PRODUCT_VARIETY_CODES.get(product)
        if not variety_code:
            continue
        try:
            response = requests.get(
                MOA_WIDE_MARKET_PRICE_URL,
                params={"varietyCode": variety_code},
                headers=MOA_HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            print(f"[RealtimeCollector] 农业农村部价格分布请求失败: {product}, {exc}")
            continue

        data = payload.get("data", {}) or {}
        for list_name in ("uplist", "downlist"):
            for item in data.get(list_name, []) or []:
                item = dict(item)
                item["sourceProduct"] = normalized_product
                item["sourceRankType"] = list_name
                records.append(item)
        time.sleep(REQUEST_DELAY_SECONDS)

    return transform_moa_wide_market_records(pd.DataFrame(records))


def transform_moa_wide_market_records(raw_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "product_name",
        "product_category",
        "market_name",
        "region",
        "date",
        "highest_price",
        "lowest_price",
        "average_price",
        "unit",
    ]
    if raw_df.empty:
        return pd.DataFrame(columns=columns)

    prices = pd.to_numeric(raw_df.get("todayPrice"), errors="coerce")
    result = pd.DataFrame({
        "product_name": raw_df.get("sourceProduct"),
        "product_category": raw_df.get("sourceProduct").map(PRODUCT_CATEGORY).fillna("其他"),
        "market_name": raw_df.get("marketName"),
        "region": raw_df.get("provinceName", pd.Series(dtype="object")).apply(parse_region),
        "date": pd.to_datetime(raw_df.get("reportTime"), errors="coerce").dt.strftime("%Y-%m-%d"),
        "highest_price": prices.round(2),
        "lowest_price": prices.round(2),
        "average_price": prices.round(2),
        "unit": raw_df.get("meteringUnit", pd.Series(dtype="object")).fillna("元/公斤"),
    })
    result = result.dropna(subset=["product_name", "market_name", "date", "average_price"])
    result = result[result["average_price"] > 0]
    return result[columns].drop_duplicates().sort_values(["date", "product_name", "region", "market_name"]).reset_index(drop=True)


def fetch_moa_market_prices(market_codes: Dict[str, str] | None = None) -> pd.DataFrame:
    market_codes = market_codes or MOA_MARKET_CODES
    records: List[Dict[str, object]] = []
    for market_label, market_code in market_codes.items():
        try:
            response = requests.get(
                MOA_MARKET_PRICE_URL,
                params={"marketCode": market_code},
                headers=MOA_HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            print(f"[RealtimeCollector] 农业农村部电子结算请求失败: {market_label}, {exc}")
            continue

        records.extend(payload.get("data", []) or [])
        time.sleep(REQUEST_DELAY_SECONDS)

    return transform_moa_market_records(pd.DataFrame(records))


def transform_moa_market_records(raw_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "product_name",
        "product_category",
        "market_name",
        "region",
        "date",
        "highest_price",
        "lowest_price",
        "average_price",
        "unit",
    ]
    if raw_df.empty:
        return pd.DataFrame(columns=columns)

    normalized_names = raw_df.apply(
        lambda row: normalize_product_name(row.get("productName"), row.get("productCode")),
        axis=1,
    )
    prices = pd.to_numeric(raw_df.get("businessPrice"), errors="coerce")
    market_names = raw_df.get("marketName", pd.Series(dtype="object")).fillna("农业农村部电子结算市场")
    result = pd.DataFrame({
        "product_name": normalized_names,
        "product_category": normalized_names.map(PRODUCT_CATEGORY).fillna("其他"),
        "market_name": market_names.apply(lambda name: f"{name}农产品大市场" if str(name) == "无锡朝阳" else str(name)),
        "region": raw_df.get("producAdd", raw_df.get("sellAdd", pd.Series(dtype="object"))).apply(parse_region),
        "date": pd.to_datetime(raw_df.get("businessDate"), errors="coerce").dt.strftime("%Y-%m-%d"),
        "highest_price": prices.round(2),
        "lowest_price": prices.round(2),
        "average_price": prices.round(2),
        "unit": "元/公斤",
    })
    result = result.dropna(subset=["product_name", "date", "average_price"])
    result = result[result["average_price"] > 0]
    if result.empty:
        return pd.DataFrame(columns=columns)

    aggregated = result.groupby([
        "product_name",
        "product_category",
        "market_name",
        "region",
        "date",
        "unit",
    ], as_index=False).agg({
        "highest_price": "max",
        "lowest_price": "min",
        "average_price": "mean",
    })
    aggregated["average_price"] = aggregated["average_price"].round(2)
    return aggregated[columns].sort_values(["date", "product_name", "region", "market_name"]).reset_index(drop=True)


def fetch_xinfadi_realtime_price(products: Iterable[str], lookback_days: int) -> pd.DataFrame:
    end = date.today()
    start = end - timedelta(days=max(0, lookback_days - 1))
    start_text = start.strftime("%Y-%m-%d")
    end_text = end.strftime("%Y-%m-%d")

    records: List[Dict[str, object]] = []
    for product in products:
        current_page = 1
        while True:
            try:
                payload = fetch_xinfadi_page(product, start_text, end_text, current_page)
            except (requests.RequestException, ValueError) as exc:
                print(f"[RealtimeCollector] 新发地价格请求失败: {product}, {exc}")
                break
            page_records = payload.get("list", []) or []
            total_count = int(payload.get("count", 0) or 0)
            if not page_records:
                break

            records.extend(page_records)
            if len(page_records) < PAGE_LIMIT or current_page * PAGE_LIMIT >= total_count:
                break

            current_page += 1
            time.sleep(REQUEST_DELAY_SECONDS)

    return transform_price_records(pd.DataFrame(records))


def fetch_realtime_price(products: Iterable[str], lookback_days: int) -> pd.DataFrame:
    frames = [
        fetch_moa_wide_market_prices(products),
        fetch_moa_market_prices(),
        fetch_xinfadi_realtime_price(products, lookback_days),
    ]
    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        return transform_price_records(pd.DataFrame())

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates(
        subset=["product_name", "market_name", "region", "date", "unit"],
        keep="last",
    )
    return combined.sort_values(["date", "product_name", "region", "market_name"]).reset_index(drop=True)


def transform_price_records(raw_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "product_name",
        "product_category",
        "market_name",
        "region",
        "date",
        "highest_price",
        "lowest_price",
        "average_price",
        "unit",
    ]
    if raw_df.empty:
        return pd.DataFrame(columns=columns)

    filtered = raw_df[raw_df["prodName"].isin(PRODUCT_NORMALIZE.keys())].copy()
    if filtered.empty:
        return pd.DataFrame(columns=columns)

    normalized_name = filtered["prodName"].map(PRODUCT_NORMALIZE)
    result = pd.DataFrame({
        "product_name": normalized_name,
        "product_category": normalized_name.map(PRODUCT_CATEGORY).fillna("其他"),
        "market_name": "北京新发地批发市场",
        "region": filtered.get("place", pd.Series(dtype="object")).apply(parse_region),
        "date": pd.to_datetime(filtered["pubDate"], errors="coerce").dt.strftime("%Y-%m-%d"),
        "highest_price": (pd.to_numeric(filtered["highPrice"], errors="coerce") * 2).round(2),
        "lowest_price": (pd.to_numeric(filtered["lowPrice"], errors="coerce") * 2).round(2),
        "average_price": (pd.to_numeric(filtered["avgPrice"], errors="coerce") * 2).round(2),
        "unit": "元/公斤",
    })
    result = result.dropna(subset=["product_name", "date", "average_price"])
    result = result[result["average_price"] > 0]
    if result.empty:
        return pd.DataFrame(columns=columns)

    aggregated = result.groupby([
        "product_name",
        "product_category",
        "market_name",
        "region",
        "date",
        "unit",
    ], as_index=False).agg({
        "highest_price": "max",
        "lowest_price": "min",
        "average_price": "mean",
    })
    aggregated["average_price"] = aggregated["average_price"].round(2)
    return aggregated[columns].sort_values(["date", "product_name", "region"]).reset_index(drop=True)


def fetch_realtime_weather(regions: Iterable[str], target_date: date) -> pd.DataFrame:
    rows = []
    for region in regions:
        coords = REGION_COORDS.get(region)
        if coords is None:
            continue
        params = {
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,sunshine_duration,weather_code",
            "forecast_days": 1,
            "timezone": "Asia/Shanghai",
        }
        try:
            response = requests.get(OPEN_METEO_FORECAST_URL, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            print(f"[RealtimeCollector] Open-Meteo 天气请求失败: {region}, {exc}")
            continue

        hourly = pd.DataFrame(payload.get("hourly", {}))
        if hourly.empty:
            continue
        hourly["time"] = pd.to_datetime(hourly["time"], errors="coerce")
        current_hours = hourly[hourly["time"].dt.date == target_date]
        if current_hours.empty:
            current_hours = hourly

        daily = payload.get("daily", {})
        weather_code = _first_value(daily.get("weather_code"))
        rainfall = _first_value(daily.get("precipitation_sum"))
        sunshine_seconds = _first_value(daily.get("sunshine_duration"))

        rows.append({
            "region": region,
            "date": target_date.strftime("%Y-%m-%d"),
            "average_temperature": round(float(pd.to_numeric(current_hours["temperature_2m"], errors="coerce").mean()), 2),
            "highest_temperature": _safe_round(_first_value(daily.get("temperature_2m_max"))),
            "lowest_temperature": _safe_round(_first_value(daily.get("temperature_2m_min"))),
            "rainfall": _safe_round(rainfall),
            "humidity": round(float(pd.to_numeric(current_hours["relative_humidity_2m"], errors="coerce").mean()), 2),
            "sunshine_duration": _safe_round(float(sunshine_seconds or 0) / 3600),
            "weather_condition": weather_code_to_condition(weather_code),
        })
        time.sleep(REQUEST_DELAY_SECONDS)

    return pd.DataFrame(rows)


def _first_value(values: object) -> object:
    if isinstance(values, list) and values:
        return values[0]
    return None


def _safe_round(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 2)


def collect_once(products: List[str], lookback_days: int) -> Dict[str, object]:
    price_df = fetch_realtime_price(products, lookback_days)
    regions = sorted(price_df["region"].dropna().unique().tolist()) if not price_df.empty else ["北京", "山东"]
    weather_df = fetch_realtime_weather(regions, date.today())
    return {
        "collected_at": datetime.now().isoformat(timespec="seconds"),
        "sources": {
            "price": [MOA_WIDE_MARKET_PRICE_URL, MOA_MARKET_PRICE_URL, XINFADI_API_URL],
            "variety_tree": MOA_VARIETY_TREE_URL,
            "weather": OPEN_METEO_FORECAST_URL,
        },
        "products": products,
        "regions": regions,
        "price_records": int(len(price_df)),
        "weather_records": int(len(weather_df)),
        "price_sample": price_df.head(1).to_dict(orient="records"),
        "weather_sample": weather_df.head(1).to_dict(orient="records"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="实时采集农产品价格和气象数据，仅用于预览采集结果")
    parser.add_argument("--products", nargs="+", default=DEFAULT_PRODUCTS, help="要采集的农产品名称")
    parser.add_argument("--lookback-days", type=int, default=3, help="向前回看天数，避免当天接口尚未更新")
    parser.add_argument("--interval-seconds", type=int, default=0, help="循环采集间隔；0 表示只采集一次")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    while True:
        summary = collect_once(args.products, args.lookback_days)
        print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
        if args.interval_seconds <= 0:
            break
        time.sleep(args.interval_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())