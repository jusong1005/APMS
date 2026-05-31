"""
Import historical processed CSV data into MongoDB.

This is a bootstrap task for old data. Realtime ingestion still uses:
Python producer -> Kafka -> Scala/Spark cleaner -> MongoDB.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from pymongo import MongoClient, UpdateOne

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRICE_CSV = PROJECT_ROOT / "data" / "processed" / "processed_price.csv"
DEFAULT_WEATHER_CSV = PROJECT_ROOT / "data" / "processed" / "processed_weather.csv"


def deterministic_id(*parts: object) -> str:
    text = "|".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def clean_text(value: Optional[str], default: Optional[str] = "") -> Optional[str]:
    text = "" if value is None else str(value).strip()
    if text:
        return text
    return default


def parse_float(value: Optional[str]) -> Optional[float]:
    text = clean_text(value, "")
    if not text:
        return None
    try:
        return round(float(text), 2)
    except ValueError:
        return None


def parse_date(value: Optional[str]) -> Optional[datetime]:
    text = clean_text(value, "")
    if not text:
        return None
    try:
        return datetime.strptime(text.replace("/", "-"), "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        return None


def iter_csv(path: Path) -> Iterable[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file_obj:
        yield from csv.DictReader(file_obj)


def raw_json(row: Dict[str, Any]) -> str:
    return json.dumps(row, ensure_ascii=False, default=str)


def build_price_doc(row: Dict[str, str], ingested_at: datetime) -> Optional[Dict[str, Any]]:
    product_name = clean_text(row.get("product_name"), "")
    market_name = clean_text(row.get("market_name"), "")
    region = clean_text(row.get("region"), "其他")
    date_value = parse_date(row.get("date"))
    unit = clean_text(row.get("unit"), "元/公斤")
    average_price = parse_float(row.get("average_price"))
    if not product_name or not market_name or date_value is None or average_price is None or average_price <= 0:
        return None

    highest_price = parse_float(row.get("highest_price")) or average_price
    lowest_price = parse_float(row.get("lowest_price")) or average_price
    if lowest_price > highest_price:
        lowest_price, highest_price = highest_price, lowest_price

    doc = {
        "_id": deterministic_id(product_name, market_name, region, date_value.date().isoformat(), unit),
        "product_name": product_name,
        "product_category": clean_text(row.get("product_category"), "其他"),
        "market_name": market_name,
        "region": region,
        "date": date_value,
        "lowest_price": lowest_price,
        "highest_price": highest_price,
        "average_price": average_price,
        "unit": unit,
        "source_url": None,
        "source_event_id": None,
        "source_topic": "historical_csv",
        "raw_json": raw_json(row),
        "ingested_at": ingested_at,
    }
    return doc


def build_weather_doc(row: Dict[str, str], ingested_at: datetime) -> Optional[Dict[str, Any]]:
    region = clean_text(row.get("region"), "")
    date_value = parse_date(row.get("date"))
    if not region or date_value is None:
        return None

    doc = {
        "_id": deterministic_id(region, date_value.date().isoformat()),
        "region": region,
        "date": date_value,
        "average_temperature": parse_float(row.get("average_temperature")),
        "highest_temperature": parse_float(row.get("highest_temperature")),
        "lowest_temperature": parse_float(row.get("lowest_temperature")),
        "rainfall": parse_float(row.get("rainfall")),
        "humidity": parse_float(row.get("humidity")),
        "sunshine_duration": parse_float(row.get("sunshine_duration")),
        "weather_condition": clean_text(row.get("weather_condition"), "未知"),
        "source_event_id": None,
        "source_topic": "historical_csv",
        "raw_json": raw_json(row),
        "ingested_at": ingested_at,
    }
    return doc


def write_batches(collection, docs: Iterable[Dict[str, Any]], batch_size: int) -> Dict[str, int]:
    scanned = 0
    skipped = 0
    inserted = 0
    operations: List[UpdateOne] = []
    for doc in docs:
        scanned += 1
        if doc is None:
            skipped += 1
            continue
        operations.append(UpdateOne({"_id": doc["_id"]}, {"$setOnInsert": doc}, upsert=True))
        if len(operations) >= batch_size:
            result = collection.bulk_write(operations, ordered=False)
            inserted += result.upserted_count
            operations.clear()
    if operations:
        result = collection.bulk_write(operations, ordered=False)
        inserted += result.upserted_count
    return {"scanned": scanned, "skipped": skipped, "inserted": inserted}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import processed historical CSV files into MongoDB")
    parser.add_argument("--mongodb-uri", default=os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017"))
    parser.add_argument("--mongodb-database", default=os.getenv("MONGODB_DATABASE", "agri_price"))
    parser.add_argument("--price-csv", type=Path, default=DEFAULT_PRICE_CSV)
    parser.add_argument("--weather-csv", type=Path, default=DEFAULT_WEATHER_CSV)
    parser.add_argument("--batch-size", type=int, default=1000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ingested_at = datetime.now(UTC)
    client = MongoClient(args.mongodb_uri)
    database = client[args.mongodb_database]
    try:
        price_result = write_batches(
            database["price_data"],
            (build_price_doc(row, ingested_at) for row in iter_csv(args.price_csv)),
            args.batch_size,
        )
        weather_result = write_batches(
            database["weather_data"],
            (build_weather_doc(row, ingested_at) for row in iter_csv(args.weather_csv)),
            args.batch_size,
        )
        print(json.dumps({"price_data": price_result, "weather_data": weather_result}, ensure_ascii=False, indent=2))
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())