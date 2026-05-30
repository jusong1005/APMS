# 数据采集脚本

## 环境准备

```bash
pip install -r requirements.txt
```

## 脚本说明

### 1. fetch_xinfadi_data.py — 农产品历史价格数据采集（真实数据）

- **数据来源**：北京新发地农产品批发市场 (http://www.xinfadi.com.cn/)
- **数据性质**：100% 真实交易数据，公开 API 获取
- **采集内容**：番茄、玉米、苹果、大白菜、白条猪的每日批发价格（最高价、最低价、均价）
- **默认时间范围**：2023-01-01 ~ 当天
- **输出文件**：合并去重写入 `data/raw/price_data.csv`

```bash
python fetch_xinfadi_data.py
```

指定日期范围和品类：

```bash
python fetch_xinfadi_data.py --start-date 2023-01-01 --end-date 2026-05-30 --products 番茄 玉米 苹果 大白菜 白条猪
```

默认会与已有 `price_data.csv` 合并去重；如果需要完全重建价格文件：

```bash
python fetch_xinfadi_data.py --replace
```

### 2. fetch_weather_data.py — 全国历史气象数据采集（真实数据）

- **数据来源**：Open-Meteo Historical Weather API（免费、无需注册）
- **数据性质**：真实历史气象观测数据（基于ERA5再分析数据集）
- **采集内容**：日均气温、最高/最低气温、降雨量、湿度、日照时长、天气状况
- **时间范围**：默认从 `data/raw/price_data.csv` 的日期范围自动推断，且不超过昨天
- **数据规模**：按全国省级地区采集，规模随价格数据时间范围变化
- **采集方式**：按日期窗口分段请求，降低长时间范围接口超时或连接重置概率
- **输出文件**：`data/raw/weather_data.csv`

```bash
python fetch_weather_data.py
```

只补指定省份：

```bash
python fetch_weather_data.py --regions 山东 河南 四川 江苏 浙江
```

默认会与已有 `weather_data.csv` 合并去重；如果需要完全重建天气文件：

```bash
python fetch_weather_data.py --replace
```

### 3. realtime_collector.py — 实时价格与气象采集

- **主价格来源**：农业农村部重点农产品市场信息平台 `https://ncpscxx.moa.gov.cn/`
- **补充价格来源**：北京新发地农产品批发市场公开接口 `http://www.xinfadi.com.cn/getPriceData.html`
- **气象来源**：Open-Meteo Forecast API `https://api.open-meteo.com/v1/forecast`
- **采集内容**：全国市场价格分布、无锡朝阳电子结算价格、近几天新发地价格记录、今日近实时气象记录
- **默认品类**：番茄、玉米、苹果、大白菜、白条猪（白条猪归一为猪肉）
- **输出文件**：追加并去重写入 `data/raw/price_data.csv` 和 `data/raw/weather_data.csv`

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

单次实时采集：

```bash
python realtime_collector.py --lookback-days 3
```

采集后立即刷新清洗后的 processed 数据：

```bash
python realtime_collector.py --lookback-days 3 --refresh-processed
```

每 10 分钟循环采集一次：

```bash
python realtime_collector.py --interval-seconds 600 --refresh-processed
```

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
| product_name | 农产品名称（番茄/玉米/苹果/大白菜/猪肉） |
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
