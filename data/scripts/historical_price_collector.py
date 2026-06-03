"""
Collect historical price records for the newly expanded product categories.

Data source:
- Beijing Xinfadi public price API: http://www.xinfadi.com.cn/getPriceData.html

The output CSV keeps the same schema as processed_price.csv so it can be
reviewed, merged, or imported into MongoDB with the existing bootstrap tools.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd
import requests

from realtime_collector import (
    DEFAULT_PRODUCTS,
    PAGE_LIMIT,
    PROJECT_ROOT,
    REQUEST_DELAY_SECONDS,
    fetch_xinfadi_page,
    transform_price_records,
)

BASELINE_PRODUCTS = {"番茄", "玉米", "苹果", "大白菜", "白条猪"}
DEFAULT_HISTORICAL_PRODUCTS = [product for product in DEFAULT_PRODUCTS if product not in BASELINE_PRODUCTS]
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "raw" / "historical_extra_price.csv"

XINFADI_HISTORICAL_QUERY_ALIASES = {
    "青椒": ["椒"],
    "尖椒": ["椒"],
    "生菜": ["生菜"],
    "菜花": ["菜花"],
    "豆角": ["豆"],
    "大米": ["大米"],
    "高粱": ["高粱", "高粱米"],
    "荞麦": ["荞麦", "荞麦面"],
    "牛肉": ["牛"],
    "羊肉": ["羊"],
    "白条鸡": ["鸡"],
    "鸡肉": ["鸡"],
    "鸭肉": ["鸭"],
    "鸡蛋": ["鸡蛋"],
}


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def date_chunks(start: date, end: date, chunk_days: int) -> Iterable[Tuple[date, date]]:
    current = start
    while current <= end:
      chunk_end = min(end, current + timedelta(days=max(1, chunk_days) - 1))
      yield current, chunk_end
      current = chunk_end + timedelta(days=1)


def product_queries(product: str) -> List[str]:
        queries = XINFADI_HISTORICAL_QUERY_ALIASES.get(product, [product])
        return list(dict.fromkeys(queries))


def fetch_page_with_retry(product: str, start_text: str, end_text: str, page: int, max_retries: int) -> dict | None:
    for attempt in range(1, max_retries + 1):
        try:
            return fetch_xinfadi_page(product, start_text, end_text, page)
        except (requests.RequestException, ValueError) as exc:
            if attempt >= max_retries:
                print(f"[HistoricalCollector] 跳过: {product} {start_text}~{end_text} 第 {page} 页, {exc}", flush=True)
                return None
            wait_seconds = min(8, attempt * 2)
            print(f"[HistoricalCollector] 重试: {product} {start_text}~{end_text} 第 {page} 页, attempt={attempt}, {exc}", flush=True)
            time.sleep(wait_seconds)
    return None


def fetch_xinfadi_history(products: List[str], start: date, end: date, chunk_days: int, max_retries: int) -> pd.DataFrame:
    raw_records = []
    queried_ranges = set()
    for product in products:
        queries = product_queries(product)
        for chunk_start, chunk_end in date_chunks(start, end, chunk_days):
            start_text = chunk_start.strftime("%Y-%m-%d")
            end_text = chunk_end.strftime("%Y-%m-%d")
            for query in queries:
                query_key = (query, start_text, end_text)
                if query_key in queried_ranges:
                    continue
                queried_ranges.add(query_key)
                print(f"[HistoricalCollector] 采集 {product}/{query}: {start_text} ~ {end_text}", flush=True)
                page = 1
                while True:
                    payload = fetch_page_with_retry(query, start_text, end_text, page, max_retries)
                    if payload is None:
                        break
                    page_records = payload.get("list", []) or []
                    total_count = int(payload.get("count", 0) or 0)
                    if not page_records:
                        break

                    raw_records.extend(page_records)
                    if len(page_records) < PAGE_LIMIT or page * PAGE_LIMIT >= total_count:
                        break

                    page += 1
                    time.sleep(REQUEST_DELAY_SECONDS)
                time.sleep(REQUEST_DELAY_SECONDS)
            time.sleep(REQUEST_DELAY_SECONDS)

    return transform_price_records(pd.DataFrame(raw_records))


def merge_existing(existing_path: Path, new_rows: pd.DataFrame) -> pd.DataFrame:
    if not existing_path.exists() or existing_path.stat().st_size == 0:
        return new_rows
    existing = pd.read_csv(existing_path)
    combined = pd.concat([existing, new_rows], ignore_index=True)
    return combined.drop_duplicates(
        subset=["product_name", "market_name", "region", "date", "unit"],
        keep="last",
    ).sort_values(["date", "product_name", "region", "market_name"]).reset_index(drop=True)


def parse_args() -> argparse.Namespace:
    default_start = date(date.today().year - 1, 1, 1).strftime("%Y-%m-%d")
    parser = argparse.ArgumentParser(description="Collect historical prices for expanded product categories")
    parser.add_argument("--products", nargs="+", default=DEFAULT_HISTORICAL_PRODUCTS, help="Products to collect")
    parser.add_argument("--start-date", default=default_start, help="Start date, YYYY-MM-DD")
    parser.add_argument("--end-date", default=date.today().strftime("%Y-%m-%d"), help="End date, YYYY-MM-DD")
    parser.add_argument("--chunk-days", type=int, default=120, help="Date range size per API sweep")
    parser.add_argument("--max-retries", type=int, default=3, help="Request retries before skipping one page")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output CSV path")
    parser.add_argument("--merge", action="store_true", help="Merge with existing output CSV before writing")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start = parse_date(args.start_date)
    end = parse_date(args.end_date)
    if start > end:
        raise ValueError("start-date must be earlier than or equal to end-date")

    rows = fetch_xinfadi_history(args.products, start, end, args.chunk_days, args.max_retries)
    output_rows = merge_existing(args.output, rows) if args.merge else rows
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_rows.to_csv(args.output, index=False, encoding="utf-8-sig")

    summary = {
        "products": args.products,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "records": int(len(output_rows)),
        "new_records": int(len(rows)),
        "output": str(args.output),
        "sample": output_rows.head(3).to_dict(orient="records"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
