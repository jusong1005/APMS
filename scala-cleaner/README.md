# Scala 实时清洗模块

本模块用于把实时链路中的数据清洗环节改为 Scala/Spark：

```text
Python 爬虫 -> Kafka 原始 Topic -> Scala Spark 清洗 -> MongoDB
```

Kafka 只负责接收和缓冲消息；字段标准化、日期格式转换、数值转换、缺失值校验、异常数据分流和去重由 Scala Spark Structured Streaming 作业完成。

## 构建

```bash
source /home/ubuntu/agri/servers/env.sh
cd /home/ubuntu/agri/code/PM/scala-cleaner
mvn -DskipTests package
```

## 运行

运行前需要 Kafka 和 MongoDB 已启动，并已创建 `raw_price_topic`、`raw_weather_topic` 等 Topic。Python 爬虫仍负责把网页/API 数据写入 Kafka 原始 Topic。

```bash
source /home/ubuntu/agri/servers/env.sh
cd /home/ubuntu/agri/code/PM/scala-cleaner

spark-submit \
  --class com.agri.pipeline.AgriKafkaMongoCleaner \
  --master local[*] \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.mongodb.spark:mongo-spark-connector_2.12:10.3.0 \
  target/agri-scala-cleaner-1.0.0.jar \
  --bootstrap-servers 127.0.0.1:9092 \
  --raw-price-topic raw_price_topic \
  --raw-weather-topic raw_weather_topic \
  --mongodb-uri mongodb://127.0.0.1:27017 \
  --mongodb-database agri_price \
  --checkpoint-dir file:///data/spark/checkpoints/agri-cleaner
```

演示时可以使用 `--once` 处理当前 Topic 中已有数据后自动退出：

```bash
spark-submit \
  --class com.agri.pipeline.AgriKafkaMongoCleaner \
  --master local[*] \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.mongodb.spark:mongo-spark-connector_2.12:10.3.0 \
  target/agri-scala-cleaner-1.0.0.jar \
  --checkpoint-dir file:///data/spark/checkpoints/agri-cleaner \
  --once
```

## 写入集合

| 集合 | 内容 |
| --- | --- |
| `price_data` | 清洗后的价格数据 |
| `weather_data` | 清洗后的气象数据 |
| `invalid_events` | 缺字段、日期非法、价格非法等异常消息 |

`price_data` 会生成基于 `product_name + market_name + region + date + unit` 的确定性 `_id`，`weather_data` 会生成基于 `region + date` 的确定性 `_id`，便于演示时识别同一业务记录。