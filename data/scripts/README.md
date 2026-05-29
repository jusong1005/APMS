# 数据采集脚本

## 环境准备

```bash
pip install -r requirements.txt
```

## 脚本说明

### 1. fetch_xinfadi_data.py — 农产品价格数据采集（真实数据）

- **数据来源**：北京新发地农产品批发市场 (http://www.xinfadi.com.cn/)
- **数据性质**：100% 真实交易数据，公开 API 获取
- **采集内容**：番茄、玉米、苹果的每日批发价格（最高价、最低价、均价）
- **时间范围**：2024-01-01 ~ 2025-04-30
- **数据规模**：约 1660 条记录
- **输出文件**：`data/raw/price_data.csv`

```bash
python fetch_xinfadi_data.py
```

### 2. fetch_weather_data.py — 气象数据采集（真实数据）

- **数据来源**：Open-Meteo Historical Weather API（免费、无需注册）
- **数据性质**：真实历史气象观测数据（基于ERA5再分析数据集）
- **采集内容**：日均气温、最高/最低气温、降雨量、湿度、日照时长、天气状况
- **时间范围**：2024-01-01 ~ 2025-04-30
- **数据规模**：972 条记录（北京 486 + 山东 486）
- **输出文件**：`data/raw/weather_data.csv`

```bash
python fetch_weather_data.py
```

## 数据特点

- ✅ **两份数据均为 100% 真实数据**
- ✅ 价格数据来自北京新发地批发市场公开 API
- ✅ 气象数据来自 Open-Meteo（基于 ERA5 再分析数据）
- ✅ 时间范围一致（2024.01 ~ 2025.04），可按 date + region 关联
- ✅ 地区一致（北京 / 山东），支持地区对比分析

## 输出数据格式

### price_data.csv

| 字段 | 说明 |
|------|------|
| product_name | 农产品名称（番茄/玉米/苹果） |
| product_category | 类别（蔬菜类/粮食类/水果类） |
| market_name | 市场名称（北京新发地批发市场） |
| region | 地区（北京/山东） |
| date | 日期 (YYYY-MM-DD) |
| highest_price | 最高价 (元/公斤) |
| lowest_price | 最低价 (元/公斤) |
| average_price | 均价 (元/公斤) |
| unit | 单位 |

### weather_data.csv

| 字段 | 说明 |
|------|------|
| region | 地区（北京/山东） |
| date | 日期 (YYYY-MM-DD) |
| average_temperature | 日均气温 (°C) |
| highest_temperature | 最高气温 (°C) |
| lowest_temperature | 最低气温 (°C) |
| rainfall | 降雨量 (mm) |
| humidity | 相对湿度 (%) |
| sunshine_duration | 日照时长 (小时) |
| weather_condition | 天气状况 |

## 数据来源引用

- 价格数据：北京新发地农产品批发市场 http://www.xinfadi.com.cn/
- 气象数据：[Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-forecast-api)
