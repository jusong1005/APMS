"""
农产品价格采集监控平台配置。

Python 侧只负责网页/API 采集并发送 Kafka；Kafka 后续清洗、入库和后端服务
由 Scala/Spark 与 Java/Spring Boot 承担。
"""

import os
from pathlib import Path

# ============================================================
# 项目根目录
# ============================================================
PROJECT_ROOT = Path(__file__).parent.resolve()

# ============================================================
# 数据文件路径配置
# ============================================================
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"

# 原始数据文件
RAW_PRICE_CSV = RAW_DATA_DIR / "price_data.csv"
RAW_WEATHER_CSV = RAW_DATA_DIR / "weather_data.csv"

# Kafka 实时链路配置
KAFKA_CONFIG = {
    "bootstrap_servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092"),
    "group_id": os.getenv("KAFKA_GROUP_ID", "agri-price-realtime-consumer"),
}

KAFKA_TOPICS = {
    "raw_price": os.getenv("KAFKA_RAW_PRICE_TOPIC", "raw_price_topic"),
    "raw_weather": os.getenv("KAFKA_RAW_WEATHER_TOPIC", "raw_weather_topic"),
}

# ============================================================
# 数据采集配置
# ============================================================
DATA_COLLECTION = {
    "min_records": 1000,          # 最低数据记录数
    "min_products": 3,            # 最少农产品种类
    "min_regions": 2,             # 最少地区数
    "min_months": 6,              # 最少时间跨度（月）
    "retry_count": 3,             # 数据获取重试次数
    "retry_interval_base": 5,     # 重试间隔基数（秒）
}

# ============================================================
