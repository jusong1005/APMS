# 农产品价格采集监控平台

## 项目简介

本项目为数科23-13第一组综合实训项目，围绕农产品价格采集监控平台完成数据采集、数据清洗、数据存储、统计分析、价格预测和可视化展示。当前架构调整为 Python 爬虫采集实时网页/API 数据，写入 Kafka 原始 Topic；Scala/Spark Structured Streaming 消费 Kafka 完成清洗并写入 MongoDB/Redis；后续由 Spring Boot 3.x 提供 API，Vue 前端展示价格趋势、地区对比、气象影响和预测结果。

项目文档按实训要求保留 Kafka、HDFS、Spark、Redis、MongoDB 等完整大数据平台架构设计；当前已删除旧 Python 后端、Python 清洗入库和预测流水线，Python 仅保留实时采集与 Kafka 生产者职责。

## 技术栈

| 模块 | 当前实现 | 扩展方案 |
| --- | --- | --- |
| 采集语言 | Python 3.10+ | 负责网页/API 采集并写入 Kafka |
| 清洗语言 | Scala 2.12.18 + Spark 3.5.1 | Structured Streaming 消费 Kafka、清洗并写入 MongoDB |
| 后端语言 | Java 17 + Spring Boot 3.x | 后续提供 REST API 和任务接口 |
| 前端框架 | Vue 3 + Vite + Tailwind CSS | DataV 监控大屏可扩展 |
| 数据存储 | MongoDB 7.0.12、Redis 7.2.5 | HDFS 历史归档可扩展 |
| 消息队列 | Kafka 3.7.0 | raw_price_topic、raw_weather_topic |
| 前端图表 | ECharts | DataV、Plotly 可扩展 |

## 项目结构

```text
PM/
├── data/
│   ├── raw/              # 历史原始样例数据
│   ├── processed/        # 历史 processed 样例数据
│   └── scripts/          # Python 实时采集和 Kafka 生产者
├── scala-cleaner/        # Scala/Spark Kafka 清洗并写 MongoDB
├── models/               # 前端/文档保留的数据结构说明
├── frontend/             # Vue 前端应用
│   ├── src/
│   │   ├── components/   # 布局、页面和通用组件
│   │   └── lib/          # 前端工具函数
│   └── package.json
├── output/               # 图表和输出结果
├── config.py             # 项目配置文件
├── requirements.txt      # Python 依赖
└── README.md             # 项目说明
```

## 核心功能

1. 数据采集：Python 获取农产品价格数据和气象辅助数据。
2. 消息传输：Python 将原始 JSON 事件发送到 Kafka。
3. 数据清洗：Scala/Spark 完成缺失值处理、异常值处理、重复值删除、字段统一和单位转换。
4. 数据存储：清洗后的价格、气象和异常数据写入 MongoDB，热点指标和预警结果进入 Redis。
5. 后端接口：后续 Spring Boot 从 MongoDB/Redis 读取数据并提供接口。
6. 可视化展示：通过 Vue + ECharts 展示概览指标、趋势图、对比图和预测结果。

## 快速开始

### Python 采集环境

```powershell
# 安装 Python 依赖
pip install -r requirements.txt

# 创建 Kafka Topic
python data/scripts/kafka_realtime_producer.py create-topics

# 采集预览，不发送 Kafka
python data/scripts/kafka_realtime_producer.py produce --lookback-days 3 --dry-run

# 采集并发送 Kafka 原始 Topic
python data/scripts/kafka_realtime_producer.py produce --lookback-days 3
```

### Scala 清洗环境

```powershell
cd scala-cleaner
mvn -DskipTests package

spark-submit --class com.agri.pipeline.AgriKafkaMongoCleaner target/agri-scala-cleaner-1.0.0.jar --once
```

清洗链路写入以下目标：

| 输出位置 | 内容 |
| --- | --- |
| Kafka raw_price_topic | Python 采集到的价格原始事件 |
| Kafka raw_weather_topic | Python 采集到的气象原始事件 |
| MongoDB agri_price.price_data | Scala/Spark 清洗后的价格数据 |
| MongoDB agri_price.weather_data | Scala/Spark 清洗后的气象数据 |
| MongoDB agri_price.invalid_events | 清洗失败或字段异常的数据 |

### 前端环境

```powershell
# 安装前端依赖
cd frontend
npm install

# 启动开发服务器
npm run dev
```

## 实训文档

| 文档 | 内容 |
| --- | --- |
| 数科23-13第一组项目需求说明书.md | 平台背景、目标、功能需求和验收标准 |
| 数科23-13第一组技术选型分析报告.md | 当前实现技术栈和完整平台扩展技术路线 |
| 数科23-13第一组资源规划报告.md | 软件、硬件、数据、人力、进度和成本规划 |
| 数科23-13第一组数据存储方案设计报告.md | 数据库选型、表结构、存储资源和成本估算 |
| 数科23-13第一组大数据质量管控方案设计报告.md | 数据质量维度、质量阈值、全流程管控和验收标准 |
| 数科23-13第一组数据入库测试记录.md | 数据完整性、格式正确性、入库一致性和基础查询测试 |
| 单节点服务器部署方案.md | 单台服务器部署、版本兼容、端口规划和验收检查清单 |

## 团队成员

| 成员 | 分工 |
| --- | --- |
| 马一凡 | 项目负责人、报告整合 |
| 盛晓宇 | 数据采集、数据来源说明 |
| 武殊宇 | 数据清洗、数据库设计、入库测试 |
| 王羽菲 | 数据分析、图表制作 |
| 靳康琦 | 模型预测、前端展示 |

## 项目说明

本项目当前版本以课程实训可运行和可验收为目标，已经将实时链路统一为“Python 爬虫 -> Kafka -> Scala/Spark 清洗 -> MongoDB/Redis -> Spring Boot/Vue”。Kafka、HDFS、Spark、Redis、MongoDB 等组件可在单节点服务器中演示完整链路，后续可在统一实验集群环境中继续部署完善。
