# 数据采集脚本

## 环境准备

```bash
pip install -r requirements.txt
```

## 脚本说明

### 1. realtime_collector.py — 实时价格与气象采集预览

- **主价格来源**：农业农村部重点农产品市场信息平台 `https://ncpscxx.moa.gov.cn/`
- **补充价格来源**：北京新发地农产品批发市场公开接口 `http://www.xinfadi.com.cn/getPriceData.html`
- **气象来源**：Open-Meteo Forecast API `https://api.open-meteo.com/v1/forecast`
- **采集内容**：全国市场价格分布、无锡朝阳电子结算价格、近几天新发地价格记录、今日近实时气象记录
- **默认品类**：蔬菜类覆盖番茄、大白菜、黄瓜、土豆、青椒、尖椒、茄子、生菜、菠菜、萝卜、胡萝卜、西兰花、菜花、油菜、芹菜、豆角；粮食类覆盖玉米、小麦、大米、大豆、高粱、小米、荞麦、绿豆；肉禽蛋类覆盖猪肉、牛肉、羊肉、鸡肉、鸭肉、鸡蛋。
- **定位**：仅负责网页/API 采集和字段提取，不做清洗、不入库

已验证可直接访问的官方接口：

| 接口 | 方法 | 用途 |
|------|------|------|
| `/product/common-price-index/getIndexByLevel` | POST | 首页农产品批发价格指数 |
| `/product/common-price-index/getIndexList?code=5` | POST | 价格指数趋势 |
| `/price_portal/sys-user-relation/getVarietiesTree` | GET | 品种树与品种编码 |
| `/product/common-price-avg/getWideMarketVarietyData?varietyCode=...` | GET | 单品种全国市场价格高低排名与地图分布 |
| `/product/piMarketPrice/getMarketDatas?marketCode=3202014` | GET | 批发市场电子结算实时交易数据 |
| `/product/FarmDaily/selectDailyList` | POST JSON | 日度价格报告列表 |
| `/product/FarmDaily/selectWeeklyList` | POST JSON | 周度价格报告列表 |

当前脚本会把官方价格源转换为统一字段：`product_name`、`product_category`、`market_name`、`region`、`date`、`highest_price`、`lowest_price`、`average_price`、`unit`。官方源不可用时，新发地接口仍会作为补充来源继续采集。

单次采集预览：

```bash
python realtime_collector.py --lookback-days 3
```

每 10 分钟循环采集一次：

```bash
python realtime_collector.py --interval-seconds 600
```

### 2. kafka_realtime_producer.py — 网页实时数据写入 Kafka

该脚本用于实现完整实时链路：

```text
网页/API 实时采集 -> raw_price_topic/raw_weather_topic -> Scala/Spark 清洗 -> MongoDB
```

Kafka 负责接收和缓冲实时消息；Python 只负责把原始采集事件写入 Kafka。字段校验、类型转换、日期标准化、异常数据分流和 MongoDB 写入由 `scala-cleaner` 模块完成。

环境变量可按需覆盖：

| 变量 | 默认值 | 说明 |
|------|------|------|
| KAFKA_BOOTSTRAP_SERVERS | 127.0.0.1:9092 | Kafka broker 地址 |
| KAFKA_GROUP_ID | agri-price-realtime-consumer | 消费者组 |
| KAFKA_RAW_PRICE_TOPIC | raw_price_topic | 原始价格数据 Topic |
| KAFKA_RAW_WEATHER_TOPIC | raw_weather_topic | 原始气象数据 Topic |

启动 Kafka 和 MongoDB 后，先创建 Topic：

```bash
python kafka_realtime_producer.py create-topics
```

只采集并查看将要发送到 Kafka 的事件数量，不连接 Kafka：

```bash
python kafka_realtime_producer.py produce --lookback-days 3 --dry-run
```

采集网页实时数据并写入 Kafka 原始 Topic：

```bash
python kafka_realtime_producer.py produce --lookback-days 3
```

每 10 分钟采集一次并持续写入 Kafka：

```bash
python kafka_realtime_producer.py produce --lookback-days 3 --interval-seconds 600
```

### 3. historical_price_collector.py — 新增品类往年价格补采

该脚本用于为扩展后的蔬菜、粮食、肉禽蛋品类补采历史价格，输出字段与 `processed_price.csv` 保持一致。脚本会按北京新发地实际商品名扩展查询词，并归一化为系统品类名称，例如“牛腩/牛前腱”归为“牛肉”，“团生菜/罗马生菜”归为“生菜”：

```bash
python historical_price_collector.py --start-date 2023-01-01 --end-date 2026-06-03 --chunk-days 60 --max-retries 3 --merge
```

默认输出：`data/raw/historical_extra_price.csv`。

## 数据特点

- ✅ **两份数据均为 100% 真实数据**
- ✅ 主价格数据来自农业农村部重点农产品市场信息平台公开接口
- ✅ 补充价格数据来自北京新发地批发市场公开 API
- ✅ 气象数据来自 Open-Meteo（基于 ERA5 再分析数据）
- ✅ 历史价格覆盖 2023.01 起，天气数据会按价格日期范围自动补齐，可按 date + region 关联
- ✅ 地区覆盖全国省级区域，支持地区对比分析
- ✅ 可通过 `realtime_collector.py` 扩展为定时实时采集

## 输出数据格式

### price_data.csv

| 字段 | 说明 |
|------|------|
| product_name | 农产品名称（番茄/大白菜/黄瓜/土豆/青椒/尖椒/茄子/生菜/菠菜/萝卜/胡萝卜/西兰花/菜花/油菜/芹菜/豆角/玉米/小麦/大米/大豆/高粱/小米/荞麦/绿豆/苹果/猪肉/牛肉/羊肉/鸡肉/鸭肉/鸡蛋） |
| product_category | 类别（蔬菜类/粮食类/水果类/肉禽蛋类） |
| market_name | 市场名称 |
| region | 地区（全国省级区域） |
| date | 日期 (YYYY-MM-DD) |
| highest_price | 最高价 (元/公斤) |
| lowest_price | 最低价 (元/公斤) |
| average_price | 均价 (元/公斤) |
| unit | 单位 |

### weather_data.csv

| 字段 | 说明 |
|------|------|
| region | 地区（全国省级区域） |
| date | 日期 (YYYY-MM-DD) |
| average_temperature | 日均气温 (°C) |
| highest_temperature | 最高气温 (°C) |
| lowest_temperature | 最低气温 (°C) |
| rainfall | 降雨量 (mm) |
| humidity | 相对湿度 (%) |
| sunshine_duration | 日照时长 (小时) |
| weather_condition | 天气状况 |

## 数据来源引用

- 价格数据：农业农村部重点农产品市场信息平台 https://ncpscxx.moa.gov.cn/
- 价格数据：北京新发地农产品批发市场 http://www.xinfadi.com.cn/
- 气象数据：[Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-forecast-api)
