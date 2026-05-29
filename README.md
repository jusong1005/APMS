# 农产品价格采集监控平台

## 项目简介

本项目为数科23-13第一组综合实训项目，围绕农产品价格采集监控平台完成数据采集、数据清洗、数据存储、统计分析、价格预测和可视化展示。平台通过整理农产品价格数据和辅助气象数据，构建结构化数据库，并以 Vue 前端 + Flask 后端的形式展示价格趋势、地区对比、气象影响和预测结果。

项目文档按实训要求保留 Kafka、HDFS、Spark、Redis、MySQL 等完整大数据平台架构设计；当前代码实现采用本地可运行的轻量方案，包括 CSV 归档、MySQL 主库、SQLite 降级测试、pandas 清洗、scikit-learn 建模和 ECharts 可视化。

## 技术栈

| 模块 | 当前实现 | 扩展方案 |
| --- | --- | --- |
| 后端语言 | Python 3.10+ | Java/SpringBoot 可扩展 |
| 前端框架 | Vue 3 + Vite | DataV 监控大屏可扩展 |
| 后端框架 | Flask | FastAPI、SpringBoot 可扩展 |
| 数据存储 | MySQL 8.0、SQLite、CSV | HDFS、Redis、Kafka 可扩展 |
| 数据处理 | pandas、NumPy | Spark、PySpark、Spark SQL 可扩展 |
| 机器学习 | scikit-learn、statsmodels | Spark MLlib、LSTM 可扩展 |
| 前端图表 | ECharts | DataV、Plotly 可扩展 |
| 测试框架 | pytest、Hypothesis | 接口测试、性能测试可扩展 |

## 项目结构

```text
PM/
├── data/
│   ├── raw/              # 原始价格和气象数据
│   ├── processed/        # 清洗后的价格、气象和合并数据
│   └── scripts/          # 数据采集脚本
├── models/               # 数据模型或结构定义
├── backend/              # Flask 后端 API 与数据处理模块
│   ├── app.py            # 应用入口
│   ├── data_collector.py # 数据采集模块
│   ├── data_cleaner.py   # 数据清洗模块
│   ├── db_importer.py    # 数据库导入模块
│   ├── data_analyzer.py  # 数据分析模块
│   ├── model_predictor.py# 模型预测模块
│   └── pipeline.py       # 项目级数据流水线
├── frontend/             # Vue 前端应用
│   ├── src/
│   │   ├── views/        # 页面组件
│   │   ├── components/   # 通用组件
│   │   ├── api/          # API 调用封装
│   │   └── router/       # 路由配置
│   └── package.json
├── tests/
│   ├── properties/       # 属性测试
│   ├── unit/             # 单元测试
│   └── integration/      # 集成测试
├── output/               # 图表和输出结果
├── config.py             # 项目配置文件
├── requirements.txt      # Python 依赖
└── README.md             # 项目说明
```

## 核心功能

1. 数据采集：获取农产品价格数据和气象辅助数据。
2. 数据清洗：完成缺失值处理、异常值处理、重复值删除、字段统一和单位转换。
3. 数据存储：设计 MySQL 表结构并导入清洗数据，支持 SQLite 降级测试。
4. 数据查询：支持按农产品、地区、日期、市场等条件查询。
5. 数据分析：完成价格趋势、地区差异、气象影响和价格波动分析。
6. 价格预测：基于历史价格和辅助特征进行价格预测，并输出误差指标。
7. 可视化展示：通过 Vue + ECharts 展示概览指标、趋势图、对比图和预测结果。
8. 测试验收：通过 pytest 和 Hypothesis 验证入库一致性和核心模块逻辑。

## 快速开始

### 后端环境

```powershell
# 安装 Python 依赖
pip install -r requirements.txt

# 一键运行完整数据流水线：清洗、合并、入库、分析、建模和摘要输出
python -m backend.pipeline

# 启动后端 API 服务
cd backend
python app.py
```

流水线执行后会生成或更新以下结果：

| 输出位置 | 内容 |
| --- | --- |
| data/processed/processed_price.csv | 清洗后的农产品价格数据 |
| data/processed/processed_weather.csv | 清洗后的气象数据 |
| data/processed/merged_data.csv | 价格与气象合并后的建模数据 |
| data/processed/cleaning_report.md | 数据清洗和质量检查报告 |
| output/charts/ | 趋势、月度、地区、气象、波动和预测评估图表 |
| output/charts/analysis_report.txt | 统计分析文字报告 |
| output/pipeline_summary.json | 本次流水线运行摘要 |
| models/random_forest_model.pkl | 随机森林价格预测模型 |

### 前端环境

```powershell
# 安装前端依赖
cd frontend
npm install

# 启动开发服务器
npm run dev
```

### 运行测试

```powershell
# 运行全部测试
pytest

# 运行数据入库一致性测试
pytest tests/properties/test_db_import.py -q

# 运行单元测试
pytest tests/unit/
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

## 团队成员

| 成员 | 分工 |
| --- | --- |
| 马一凡 | 项目负责人、报告整合 |
| 盛晓宇 | 数据采集、数据来源说明 |
| 武殊宇 | 数据清洗、数据库设计、入库测试 |
| 王羽菲 | 数据分析、图表制作 |
| 靳康琦 | 模型预测、前端展示 |

## 项目说明

本项目当前版本以课程实训可运行和可验收为目标，已经完成农产品价格数据、气象辅助数据、结构化存储、基础查询、预测分析和可视化展示的核心流程。Kafka、HDFS、Spark、Redis 等组件在文档中作为完整农产品价格采集监控平台的扩展架构说明，后续可在统一实验集群环境中继续部署完善。
