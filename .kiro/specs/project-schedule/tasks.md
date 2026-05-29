# 实施计划：农产品价格采集监控平台

## 概述

本实施计划将农产品价格采集监控平台设计分解为可执行的编码任务，按照数据处理流水线顺序实现：数据采集→数据清洗→数据存储→数据分析→模型预测→可视化展示。每个任务构建在前一步骤之上，确保增量式开发和验证。

## 任务

- [x] 1. 项目结构搭建与核心接口定义
  - [x] 1.1 创建项目目录结构和基础配置文件
    - 创建以下目录结构：`data/raw/`、`data/processed/`、`models/`、`backend/`、`frontend/`、`tests/properties/`、`tests/unit/`、`tests/integration/`
    - 创建 `requirements.txt`（包含 pandas、numpy、scikit-learn、statsmodels、flask、pymysql、hypothesis、pytest）
    - 创建 `README.md` 项目说明文件
    - 创建 `config.py` 配置文件（数据库连接、文件路径等）
    - _需求：7.4, 7.3_

  - [x] 1.2 定义核心数据类和接口类型
    - 在 `models/schemas.py` 中定义 `CleaningReport`、`QualityResult`、`AnalysisResult`、`ModelMetrics` 数据类
    - 定义 MySQL 表对应的 Python 数据模型（price_data、weather_data）
    - _需求：3.1, 2.4_

- [x] 2. 数据采集模块实现
  - [x] 2.1 实现数据采集核心逻辑（data_collector.py）
    - 实现 `DataCollector` 类，包含 `collect_price_data()`、`collect_weather_data()` 方法
    - 实现 `load_kaggle_backup()` 方法加载备选数据集
    - 实现 `validate_sufficiency()` 方法验证数据量（≥1000条、≥3种农产品、≥2个地区、≥6个月）
    - 实现 `validate_alignment()` 方法验证价格和气象数据的地区/时间对齐
    - 输出 CSV 格式原始数据文件和数据来源说明文档
    - _需求：1.1, 1.2, 1.3, 1.4_

  - [x] 2.2 编写属性测试：数据充分性验证
    - **属性 1：数据充分性验证**
    - 随机生成数据集元信息（记录数0-5000、时间范围0-24月、品种数1-10、地区数1-5），验证充分性判定逻辑
    - **验证需求：1.1**

  - [x] 2.3 编写属性测试：数据对齐验证
    - **属性 2：数据对齐验证**
    - 随机生成价格和气象数据的地区/时间组合，验证对齐判定逻辑
    - **验证需求：1.2**

- [x] 3. 数据清洗模块实现
  - [x] 3.1 实现数据清洗核心逻辑（data_cleaner.py）
    - 实现 `DataCleaner` 类，包含完整清洗流程 `clean()` 方法
    - 实现 `handle_missing_values()`：缺失比例<50%用均值/众数填充，≥50%删除字段
    - 实现 `handle_outliers()`：对价格和气象数值字段使用IQR方法修正异常值为边界值
    - 实现 `remove_duplicates()`：基于全部字段完全相同的记录去重
    - 实现 `standardize_format()`：日期统一YYYY-MM-DD，价格统一元/公斤
    - 实现 `merge_data()`：按date和region字段关联合并价格和气象数据
    - 实现 `validate_quality()`：缺失>20%或重复>10%标记不达标
    - 输出 processed_price.csv 和 processed_weather.csv，生成清洗报告
    - _需求：2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.2 编写属性测试：数据清洗规则正确性
    - **属性 3：数据清洗规则正确性**
    - 随机生成含缺失值、异常值、重复记录的DataFrame，验证清洗规则
    - **验证需求：2.1, 2.3**

  - [x] 3.3 编写属性测试：数据关联合并正确性
    - **属性 4：数据关联合并正确性**
    - 随机生成价格和气象DataFrame，验证merge后每条记录包含对应日期和地区的完整信息
    - **验证需求：2.2**

  - [x] 3.4 编写属性测试：清洗后数据质量阈值判定
    - **属性 5：清洗后数据质量阈值判定**
    - 随机生成缺失比例(0-1)和重复比例(0-1)，验证质量判定逻辑
    - **验证需求：2.5**

- [x] 4. 检查点 - 确保数据处理模块测试通过
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 5. 数据存储模块实现
  - [x] 5.1 实现MySQL数据库建表和数据导入（db_importer.py）
    - 创建 `schema.sql` 文件定义 price_data 和 weather_data 表结构
    - 实现 `DBImporter` 类，包含 `import_price_data()`、`import_weather_data()` 方法
    - 实现 `verify_import()` 方法验证导入后记录数与CSV行数一致
    - 实现 `fallback_to_sqlite()` 方法，MySQL不可用时降级为SQLite
    - _需求：3.1, 3.2, 3.3_

  - [x] 5.2 编写属性测试：数据导入一致性
    - **属性 6：数据导入一致性**
    - 随机生成不同行数的CSV数据，验证导入后MySQL/SQLite记录数与CSV行数一致
    - **验证需求：3.2**

- [x] 6. 数据分析模块实现
  - [x] 6.1 实现统计分析核心逻辑（data_analyzer.py）
    - 实现 `DataAnalyzer` 类
    - 实现 `analyze_price_trend()`：价格趋势分析，生成折线图
    - 实现 `analyze_monthly_price()`：月度价格分析，生成柱状图
    - 实现 `analyze_regional_difference()`：地区差异分析，生成对比图
    - 实现 `analyze_weather_correlation()`：气象影响分析，生成相关性热力图
    - 实现 `analyze_price_volatility()`：价格波动分析，生成波动图
    - 实现 `generate_report()`：生成不少于500字的统计分析报告
    - 每张图表须包含标题、坐标轴标签和数据来源说明
    - _需求：4.1, 4.2, 4.3_

  - [x] 6.2 编写属性测试：图表元数据完整性
    - **属性 7：图表元数据完整性**
    - 随机生成分析数据，验证每张图表输出包含非空标题、坐标轴标签和数据来源说明
    - **验证需求：4.2**

- [x] 7. 模型预测模块实现
  - [x] 7.1 实现随机森林预测模型（model_predictor.py）
    - 实现 `ModelPredictor` 类
    - 实现 `engineer_features()`：添加时间特征、季节特征和地区编码特征
    - 实现 `train_random_forest()`：训练随机森林回归模型（训练数据≥100条）
    - 实现 `evaluate_model()`：计算MAE、MSE、RMSE指标，生成真实值与预测值对比图
    - 实现 `save_model()` 和 `load_model()`：模型序列化保存和加载
    - _需求：5.1, 5.2, 5.3, 5.5_

  - [x] 7.2 实现ARIMA备选模型和应急触发逻辑
    - 实现 `train_arima()`：训练ARIMA时间序列模型
    - 实现 `should_trigger_arima()`：RMSE>均价30%或R²<0.5时触发
    - 当触发时输出两个模型的误差指标对比结果
    - _需求：5.4_

  - [x] 7.3 编写属性测试：模型序列化往返
    - **属性 8：模型序列化往返**
    - 训练随机数据模型，序列化保存后再加载，验证相同测试数据预测结果完全一致
    - **验证需求：5.3**

  - [x] 7.4 编写属性测试：模型性能应急触发正确性
    - **属性 9：模型性能应急触发正确性**
    - 随机生成ModelMetrics（RMSE、R²、均价），验证应急触发逻辑正确性
    - **验证需求：5.4**

- [x] 8. 检查点 - 确保数据分析和模型模块测试通过
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 9. 后端API实现
  - [x] 9.1 实现Flask/FastAPI后端REST API（app.py）
    - 创建 Flask/FastAPI 应用入口
    - 实现 `/api/overview` 接口：返回数据集基本统计信息和数据量
    - 实现 `/api/price-trends` 接口：返回价格趋势数据，支持按product和region参数筛选
    - 实现 `/api/weather-impact` 接口：返回气象因素与价格的相关性矩阵数据
    - 实现 `/api/predictions` 接口：返回预测结果对比数据和模型误差指标
    - 配置CORS支持前端跨域请求
    - 确保通过 `python app.py` 可正常启动
    - _需求：6.1, 6.4_

  - [x] 9.2 编写API接口单元测试
    - 测试各接口返回正确JSON格式
    - 测试筛选参数的正确处理
    - 测试无数据时的空结果处理
    - _需求：6.1, 6.4_

- [x] 10. 前端Vue.js应用实现
  - [x] 10.1 搭建Vue.js 3 + Vite前端项目结构
    - 使用Vite创建Vue.js 3项目
    - 配置路由（vue-router）：四个页面路由
    - 安装并配置ECharts/Chart.js图表库
    - 创建 `api/index.js` API调用封装模块
    - 创建 `NavBar.vue` 导航栏组件和 `ChartContainer.vue` 图表容器组件
    - _需求：6.2, 6.3_

  - [x] 10.2 实现数据概览页（OverviewPage.vue）
    - 调用 `/api/overview` 接口获取数据
    - 展示数据集基本统计信息和数据量
    - _需求：6.2_

  - [x] 10.3 实现价格趋势分析页（PriceTrendPage.vue）
    - 调用 `/api/price-trends` 接口获取数据
    - 使用ECharts渲染交互式价格折线图
    - 实现按农产品和地区的筛选功能
    - _需求：6.2_

  - [x] 10.4 实现气象影响分析页（WeatherImpactPage.vue）
    - 调用 `/api/weather-impact` 接口获取数据
    - 使用ECharts渲染气象因素与价格的相关性热力图
    - _需求：6.2_

  - [x] 10.5 实现价格预测展示页（PredictionPage.vue）
    - 调用 `/api/predictions` 接口获取数据
    - 展示预测结果对比图和模型误差指标
    - _需求：6.2_

- [x] 11. 检查点 - 确保前后端可正常启动和交互
  - 确保 `python app.py` 可正常启动后端
  - 确保 `npm run serve` 可正常启动前端
  - 确保四个页面均可正常访问并展示后端数据
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 12. 工作量均衡验证与项目配置
  - [x] 12.1 实现工作量均衡验证逻辑
    - 在 `config.py` 或独立模块中实现工作量验证函数
    - 验证每位成员每周≤20工时
    - 验证任意两周之间团队总工作量差异不超过较大值的30%
    - _需求：7.2_

  - [x] 12.2 编写属性测试：工作量均衡约束
    - **属性 10：工作量均衡约束**
    - 随机生成任务分配方案（工时1-25h），验证约束判定逻辑
    - **验证需求：7.2**

- [x] 13. 最终检查点 - 确保全部测试通过
  - 确保所有测试通过，如有问题请向用户确认。

## 备注

- 标记 `*` 的任务为可选任务，可跳过以加快MVP开发
- 每个任务引用具体需求编号以确保可追溯性
- 检查点确保增量式验证
- 属性测试验证数据处理和模型逻辑的普遍正确性
- 单元测试验证具体场景和边界条件
- 系统仅包含2张MySQL表：price_data 和 weather_data
- 技术栈：Python 3.10+（后端）、Vue.js 3 + Vite（前端）、MySQL 8.0（SQLite降级）、scikit-learn + statsmodels（ML）

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["2.1"] },
    { "id": 3, "tasks": ["2.2", "2.3", "3.1"] },
    { "id": 4, "tasks": ["3.2", "3.3", "3.4", "5.1"] },
    { "id": 5, "tasks": ["5.2", "6.1"] },
    { "id": 6, "tasks": ["6.2", "7.1"] },
    { "id": 7, "tasks": ["7.2", "7.3", "7.4"] },
    { "id": 8, "tasks": ["9.1", "12.1"] },
    { "id": 9, "tasks": ["9.2", "10.1", "12.2"] },
    { "id": 10, "tasks": ["10.2", "10.3", "10.4", "10.5"] }
  ]
}
```
