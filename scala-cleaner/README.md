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
  --checkpoint-dir file:///data/spark/checkpoints/agri-cleaner \
  --processing-interval "10 minutes" \
  --redis-host 127.0.0.1 \
  --redis-port 6379 \
  --redis-key-prefix agri:realtime
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

## Redis 实时结果

实时清洗作业默认每 10 分钟处理一批 Kafka 数据。价格批次在写入 MongoDB 后，会同步把最新批次指标、最新价格、分组均价和预警结果写入 Redis。

| Redis key | 内容 |
| --- | --- |
| `agri:realtime:last_batch` | 最新批次汇总，包含批次 ID、数据量、实时平均价格、预警数量和处理时间 |
| `agri:realtime:latest_prices` | 最新批次价格明细，默认最多保存 200 条 |
| `agri:realtime:metrics` | Hash 结构，保存 `latest_batch_count`、`realtime_average_price`、`alert_count`、`last_processed_at` |
| `agri:realtime:latest_alerts` | 最新批次价格异常波动预警列表 |
| `agri:realtime:baseline:product_region_avg_price` | Hash 结构，保存每个产品和地区上一批平均价，用于下一批异常波动检测 |
| `agri:realtime:product_region_stats` | Hash 结构，保存最新批次各产品和地区的记录数、均价、最低价、最高价 |

异常波动检测默认阈值是 20%。当某个产品和地区本批均价相对上一批均价涨跌幅超过阈值时，会写入 `agri:realtime:latest_alerts`。

查看 Redis 实时结果：

```bash
source /home/ubuntu/agri/servers/env.sh
redis-cli get agri:realtime:last_batch
redis-cli hgetall agri:realtime:metrics
redis-cli get agri:realtime:latest_alerts
```

## 历史数据 Spark 分析

历史数据分析作业从 HDFS 读取 processed CSV，输出统计分析、趋势分析、关联分析、Spark SQL 查询分析和价格波动分析结果。

上传历史数据到 HDFS：

```bash
source /home/ubuntu/agri/servers/env.sh
hdfs dfs -mkdir -p /agri_price/processed /agri_price/output/analysis
hdfs dfs -put -f /home/ubuntu/agri/code/PM/data/processed/processed_price.csv /agri_price/processed/processed_price.csv
hdfs dfs -put -f /home/ubuntu/agri/code/PM/data/processed/processed_weather.csv /agri_price/processed/processed_weather.csv
hdfs dfs -put -f /home/ubuntu/agri/code/PM/data/processed/merged_data.csv /agri_price/processed/merged_data.csv
```

运行历史分析：

```bash
source /home/ubuntu/agri/servers/env.sh
cd /home/ubuntu/agri/code/PM/scala-cleaner
mvn -DskipTests package

spark-submit \
  --class com.agri.pipeline.AgriHistoricalAnalysis \
  --master local[*] \
  target/agri-scala-cleaner-1.0.0.jar \
  --price-path /agri_price/processed/processed_price.csv \
  --weather-path /agri_price/processed/processed_weather.csv \
  --merged-path /agri_price/processed/merged_data.csv \
  --output-path /agri_price/output/analysis
```

主要输出目录：

| HDFS 目录 | 内容 |
| --- | --- |
| `/agri_price/output/analysis/overview` | 总体记录数、日期范围、均值、中位数、标准差 |
| `/agri_price/output/analysis/product_statistics` | 按产品统计均值、中位数、标准差、最高价、最低价 |
| `/agri_price/output/analysis/region_statistics` | 按地区统计价格水平 |
| `/agri_price/output/analysis/region_price_difference` | 按产品对比不同地区价格差异和偏离幅度 |
| `/agri_price/output/analysis/yearly_trend` | 分析 2023 到 2026 年按产品的年度价格趋势 |
| `/agri_price/output/analysis/daily_trend` | 按产品和日期计算趋势、涨跌额和涨跌幅 |
| `/agri_price/output/analysis/seasonal_price_change` | 按春夏秋冬分析不同产品和地区的季节性价格变化 |
| `/agri_price/output/analysis/price_range_analysis` | 统计历史最低价、最高价、波动区间和区间波动率 |
| `/agri_price/output/analysis/volatility_analysis` | 按产品和地区分析价格波动规律 |
| `/agri_price/output/analysis/weather_correlation` | 分析价格与温度、降雨量、湿度、日照时长的相关性 |
| `/agri_price/output/analysis/spark_sql_analysis` | 使用 Spark SQL 完成产品、地区、气象综合查询分析 |
| `/agri_price/output/analysis/top_fluctuations` | 输出价格波动幅度最大的记录 |