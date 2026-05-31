"""
Realtime producer: Python crawler -> Kafka raw topics.

Python stops at Kafka. Scala/Spark handles cleaning and MongoDB persistence.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from config import KAFKA_CONFIG, KAFKA_TOPICS
from data.scripts.realtime_collector import (
    DEFAULT_PRODUCTS,
    fetch_realtime_price,
    fetch_realtime_weather,
)


def split_bootstrap_servers(value: str) -> List[str]:
    return [server.strip() for server in value.split(",") if server.strip()]


def utc_now_text() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def json_serializer(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, default=str).encode("utf-8")


def dataframe_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    if df.empty:
        return []
    return df.where(pd.notnull(df), None).to_dict(orient="records")


def make_envelope(event_type: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "event_id": uuid.uuid4().hex,
        "event_type": event_type,
        "collected_at": utc_now_text(),
        "payload": dict(payload),
    }


def make_record_key(event_type: str, payload: Mapping[str, Any]) -> str:
    if event_type == "price":
        key_parts = [
            payload.get("product_name"),
            payload.get("market_name"),
            payload.get("region"),
            payload.get("date"),
            payload.get("unit"),
        ]
    else:
        key_parts = [payload.get("region"), payload.get("date")]
    return "|".join(str(part or "") for part in key_parts)


def get_kafka_producer():
    from kafka import KafkaProducer

    return KafkaProducer(
        bootstrap_servers=split_bootstrap_servers(KAFKA_CONFIG["bootstrap_servers"]),
        key_serializer=lambda value: value.encode("utf-8") if value else None,
        value_serializer=json_serializer,
    )


def create_topics() -> Dict[str, Any]:
    from kafka.admin import KafkaAdminClient, NewTopic
    from kafka.errors import TopicAlreadyExistsError

    admin = KafkaAdminClient(
        bootstrap_servers=split_bootstrap_servers(KAFKA_CONFIG["bootstrap_servers"]),
        client_id="agri-price-topic-admin",
    )
    topic_names = list(dict.fromkeys(KAFKA_TOPICS.values()))
    topics = [NewTopic(name=name, num_partitions=1, replication_factor=1) for name in topic_names]
    try:
        admin.create_topics(new_topics=topics, validate_only=False)
        created = topic_names
    except TopicAlreadyExistsError:
        created = []
    finally:
        admin.close()
    return {"topics": topic_names, "created": created}


def collect_events(products: List[str], lookback_days: int) -> Dict[str, Any]:
    price_df = fetch_realtime_price(products, lookback_days)
    regions = sorted(price_df["region"].dropna().unique().tolist()) if not price_df.empty else ["北京", "山东"]
    weather_df = fetch_realtime_weather(regions, date.today())
    return {
        "price": [make_envelope("price", record) for record in dataframe_records(price_df)],
        "weather": [make_envelope("weather", record) for record in dataframe_records(weather_df)],
    }


def produce_once(products: List[str], lookback_days: int, dry_run: bool) -> Dict[str, Any]:
    events = collect_events(products, lookback_days)
    summary = {
        "collected_at": utc_now_text(),
        "price_events": len(events["price"]),
        "weather_events": len(events["weather"]),
        "topics": {
            "price": KAFKA_TOPICS["raw_price"],
            "weather": KAFKA_TOPICS["raw_weather"],
        },
    }
    if dry_run:
        summary["sample"] = {
            "price": events["price"][:1],
            "weather": events["weather"][:1],
        }
        return summary

    producer = get_kafka_producer()
    try:
        for envelope in events["price"]:
            payload = envelope["payload"]
            producer.send(KAFKA_TOPICS["raw_price"], key=make_record_key("price", payload), value=envelope)
        for envelope in events["weather"]:
            payload = envelope["payload"]
            producer.send(KAFKA_TOPICS["raw_weather"], key=make_record_key("weather", payload), value=envelope)
        producer.flush()
    finally:
        producer.close()
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Python crawler -> Kafka raw topic producer")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("create-topics", help="Create Kafka raw topics")

    produce_parser = subparsers.add_parser("produce", help="Fetch realtime web data and send raw events to Kafka")
    produce_parser.add_argument("--products", nargs="+", default=DEFAULT_PRODUCTS, help="Products to collect")
    produce_parser.add_argument("--lookback-days", type=int, default=3, help="Price lookback days")
    produce_parser.add_argument("--interval-seconds", type=int, default=0, help="Loop interval; 0 means run once")
    produce_parser.add_argument("--dry-run", action="store_true", help="Fetch and print event counts without Kafka")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "create-topics":
        print(json.dumps(create_topics(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "produce":
        while True:
            summary = produce_once(args.products, args.lookback_days, args.dry_run)
            print(json.dumps(summary, ensure_ascii=False, indent=2, default=str), flush=True)
            if args.interval_seconds <= 0:
                break
            time.sleep(args.interval_seconds)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())