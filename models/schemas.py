"""
核心数据类和接口类型定义

定义系统中使用的核心数据结构，包括：
- CleaningReport: 数据清洗报告
- QualityResult: 数据质量检查结果
- AnalysisResult: 统计分析结果
- ModelMetrics: 模型评估指标
- PriceData: 农产品价格数据模型（对应 MySQL price_data 表）
- WeatherData: 气象数据模型（对应 MySQL weather_data 表）
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional


@dataclass
class CleaningReport:
    """数据清洗报告

    记录数据清洗过程中的各项处理统计信息。

    Attributes:
        original_records: 清洗前原始记录数
        cleaned_records: 清洗后记录数
        missing_values_filled: 各字段缺失值填充数量 {字段名: 填充数量}
        fields_dropped: 因缺失比例>=50%被删除的字段列表
        outliers_fixed: 各字段异常值修正数量 {字段名: 修正数量}
        duplicates_removed: 删除的重复记录数
        missing_ratio_after: 清洗后缺失值比例
        duplicate_ratio_after: 清洗后重复记录比例
    """

    original_records: int
    cleaned_records: int
    missing_values_filled: Dict[str, int]
    fields_dropped: List[str]
    outliers_fixed: Dict[str, int]
    duplicates_removed: int
    missing_ratio_after: float
    duplicate_ratio_after: float


@dataclass
class QualityResult:
    """数据质量检查结果

    用于判定清洗后数据是否达到质量标准。
    当缺失比例>20%或重复比例>10%时标记为不达标。

    Attributes:
        is_acceptable: 数据质量是否达标
        missing_ratio: 当前缺失值比例
        duplicate_ratio: 当前重复记录比例
        issues: 质量问题描述列表
    """

    is_acceptable: bool
    missing_ratio: float
    duplicate_ratio: float
    issues: List[str]


@dataclass
class AnalysisResult:
    """统计分析结果

    封装单次统计分析的输出，包括图表数据和描述信息。

    Attributes:
        analysis_type: 分析类型 (trend/monthly/regional/weather/volatility)
        title: 分析标题
        chart_data: 图表数据字典
        chart_path: 图表文件保存路径（可选）
        description: 分析结论描述
    """

    analysis_type: str
    title: str
    chart_data: dict
    chart_path: Optional[str] = None
    description: str = ""


@dataclass
class ModelMetrics:
    """模型评估指标

    记录预测模型的性能评估结果。

    Attributes:
        mae: 平均绝对误差 (Mean Absolute Error)
        mse: 均方误差 (Mean Squared Error)
        rmse: 均方根误差 (Root Mean Squared Error)
        r_squared: 决定系数 R²（可选）
        test_set_mean_price: 测试集平均价格（可选，用于判断是否触发ARIMA）
        training_records: 训练数据记录数
    """

    mae: float
    mse: float
    rmse: float
    r_squared: Optional[float] = None
    test_set_mean_price: Optional[float] = None
    training_records: int = 0


# ============================================================
# MySQL 表对应的 Python 数据模型
# ============================================================


@dataclass
class PriceData:
    """农产品价格数据模型

    对应 MySQL price_data 表结构。

    表结构:
        CREATE TABLE price_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_name VARCHAR(50) NOT NULL,
            product_category VARCHAR(50) NOT NULL,
            market_name VARCHAR(100) NOT NULL,
            region VARCHAR(50) NOT NULL,
            date DATE NOT NULL,
            highest_price DECIMAL(10,2),
            lowest_price DECIMAL(10,2),
            average_price DECIMAL(10,2) NOT NULL,
            unit VARCHAR(20) DEFAULT '元/公斤',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )

    Attributes:
        product_name: 农产品名称
        product_category: 农产品类别
        market_name: 市场名称
        region: 地区
        date: 日期
        average_price: 均价（元/公斤），必填
        highest_price: 最高价（元/公斤）
        lowest_price: 最低价（元/公斤）
        unit: 价格单位，默认"元/公斤"
        id: 主键ID（数据库自增，可选）
        created_at: 创建时间（数据库自动生成，可选）
    """

    product_name: str
    product_category: str
    market_name: str
    region: str
    date: date
    average_price: float
    highest_price: Optional[float] = None
    lowest_price: Optional[float] = None
    unit: str = "元/公斤"
    id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class WeatherData:
    """气象数据模型

    对应 MySQL weather_data 表结构。

    表结构:
        CREATE TABLE weather_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            region VARCHAR(50) NOT NULL,
            date DATE NOT NULL,
            average_temperature DECIMAL(5,2),
            highest_temperature DECIMAL(5,2),
            lowest_temperature DECIMAL(5,2),
            rainfall DECIMAL(8,2),
            humidity DECIMAL(5,2),
            sunshine_duration DECIMAL(5,2),
            weather_condition VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )

    Attributes:
        region: 地区
        date: 日期
        average_temperature: 日均气温（°C）
        highest_temperature: 最高气温（°C）
        lowest_temperature: 最低气温（°C）
        rainfall: 降雨量（mm）
        humidity: 相对湿度（%）
        sunshine_duration: 日照时长（小时）
        weather_condition: 天气状况
        id: 主键ID（数据库自增，可选）
        created_at: 创建时间（数据库自动生成，可选）
    """

    region: str
    date: date
    average_temperature: Optional[float] = None
    highest_temperature: Optional[float] = None
    lowest_temperature: Optional[float] = None
    rainfall: Optional[float] = None
    humidity: Optional[float] = None
    sunshine_duration: Optional[float] = None
    weather_condition: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
