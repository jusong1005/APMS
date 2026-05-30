"""
属性测试：图表元数据完整性

Feature: project-schedule, Property 7: 图表元数据完整性

**Validates: Requirements 4.2**

对于任何生成的统计分析图表，图表应包含标题（非空字符串）、
坐标轴标签（非空字符串）和数据来源说明（非空字符串）。
"""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from hypothesis import given, settings, assume
from hypothesis import strategies as st

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from backend.data_analyzer import DataAnalyzer


# ============================================================
# 策略：生成分析所需的随机DataFrame
# ============================================================

PRODUCT_NAMES = ["番茄", "黄瓜", "白菜", "土豆", "苹果", "香蕉", "西瓜", "大蒜"]
REGION_NAMES = ["北京", "上海", "广州", "成都", "武汉", "西安", "杭州", "南京"]


@st.composite
def price_dataframe_strategy(draw):
    """生成包含 date、product_name、region、average_price 列的随机DataFrame。

    确保至少有5行数据、至少1种产品、至少1个地区、至少2个不同日期。
    """
    n_rows = draw(st.integers(min_value=5, max_value=50))
    n_products = draw(st.integers(min_value=1, max_value=min(4, len(PRODUCT_NAMES))))
    n_regions = draw(st.integers(min_value=1, max_value=min(3, len(REGION_NAMES))))

    products = PRODUCT_NAMES[:n_products]
    regions = REGION_NAMES[:n_regions]

    # 生成日期范围（至少跨2个月）
    start_date = pd.Timestamp("2023-01-01")
    dates = pd.date_range(start=start_date, periods=max(n_rows, 60), freq="D")

    records = []
    for i in range(n_rows):
        records.append({
            "date": dates[i % len(dates)],
            "product_name": products[i % n_products],
            "region": regions[i % n_regions],
            "average_price": draw(st.floats(min_value=0.5, max_value=100.0, allow_nan=False, allow_infinity=False)),
            "highest_price": draw(st.floats(min_value=1.0, max_value=150.0, allow_nan=False, allow_infinity=False)),
            "lowest_price": draw(st.floats(min_value=0.1, max_value=80.0, allow_nan=False, allow_infinity=False)),
        })

    return pd.DataFrame(records)


@st.composite
def weather_dataframe_strategy(draw):
    """生成包含气象字段和价格字段的随机DataFrame，用于气象相关性分析。

    确保数据有足够的方差（不全为常数），以避免相关系数全为NaN。
    """
    n_rows = draw(st.integers(min_value=10, max_value=50))

    records = []
    for _ in range(n_rows):
        records.append({
            "average_price": draw(st.floats(min_value=0.5, max_value=100.0, allow_nan=False, allow_infinity=False)),
            "highest_price": draw(st.floats(min_value=1.0, max_value=150.0, allow_nan=False, allow_infinity=False)),
            "lowest_price": draw(st.floats(min_value=0.1, max_value=80.0, allow_nan=False, allow_infinity=False)),
            "average_temperature": draw(st.floats(min_value=-10.0, max_value=40.0, allow_nan=False, allow_infinity=False)),
            "highest_temperature": draw(st.floats(min_value=-5.0, max_value=45.0, allow_nan=False, allow_infinity=False)),
            "lowest_temperature": draw(st.floats(min_value=-20.0, max_value=30.0, allow_nan=False, allow_infinity=False)),
            "rainfall": draw(st.floats(min_value=0.0, max_value=200.0, allow_nan=False, allow_infinity=False)),
            "humidity": draw(st.floats(min_value=10.0, max_value=100.0, allow_nan=False, allow_infinity=False)),
            "sunshine_duration": draw(st.floats(min_value=0.0, max_value=14.0, allow_nan=False, allow_infinity=False)),
        })

    df = pd.DataFrame(records)
    # 确保至少 average_price 列有方差（不全为同一值），
    # 这样相关系数矩阵不会全为NaN
    assume(df["average_price"].std() > 0)
    return df


# ============================================================
# 辅助函数：验证图表元数据
# ============================================================

def assert_chart_metadata_complete(result, analysis_name: str):
    """验证 AnalysisResult 的图表元数据完整性。

    检查：
    - result.title 非空字符串
    - chart_data['title'] 非空字符串
    - chart_data['xlabel'] 非空字符串
    - chart_data['ylabel'] 非空字符串
    - chart_data['data_source'] 非空字符串
    """
    # 验证 result.title 非空
    assert isinstance(result.title, str) and len(result.title.strip()) > 0, (
        f"[{analysis_name}] result.title 应为非空字符串，实际值: '{result.title}'"
    )

    # 验证 chart_data 存在且为字典
    assert isinstance(result.chart_data, dict), (
        f"[{analysis_name}] chart_data 应为字典类型，实际类型: {type(result.chart_data)}"
    )

    # 验证 chart_data['title'] 非空
    assert "title" in result.chart_data, (
        f"[{analysis_name}] chart_data 缺少 'title' 键"
    )
    assert isinstance(result.chart_data["title"], str) and len(result.chart_data["title"].strip()) > 0, (
        f"[{analysis_name}] chart_data['title'] 应为非空字符串，实际值: '{result.chart_data.get('title')}'"
    )

    # 验证 chart_data['xlabel'] 非空
    assert "xlabel" in result.chart_data, (
        f"[{analysis_name}] chart_data 缺少 'xlabel' 键"
    )
    assert isinstance(result.chart_data["xlabel"], str) and len(result.chart_data["xlabel"].strip()) > 0, (
        f"[{analysis_name}] chart_data['xlabel'] 应为非空字符串，实际值: '{result.chart_data.get('xlabel')}'"
    )

    # 验证 chart_data['ylabel'] 非空
    assert "ylabel" in result.chart_data, (
        f"[{analysis_name}] chart_data 缺少 'ylabel' 键"
    )
    assert isinstance(result.chart_data["ylabel"], str) and len(result.chart_data["ylabel"].strip()) > 0, (
        f"[{analysis_name}] chart_data['ylabel'] 应为非空字符串，实际值: '{result.chart_data.get('ylabel')}'"
    )

    # 验证 chart_data['data_source'] 非空
    assert "data_source" in result.chart_data, (
        f"[{analysis_name}] chart_data 缺少 'data_source' 键"
    )
    assert isinstance(result.chart_data["data_source"], str) and len(result.chart_data["data_source"].strip()) > 0, (
        f"[{analysis_name}] chart_data['data_source'] 应为非空字符串，实际值: '{result.chart_data.get('data_source')}'"
    )


# ============================================================
# 属性测试
# ============================================================

@settings(max_examples=100, deadline=None)
@given(df=price_dataframe_strategy())
def test_price_trend_chart_metadata(df: pd.DataFrame):
    """属性测试：价格趋势分析图表元数据完整性

    Feature: project-schedule, Property 7: 图表元数据完整性

    **Validates: Requirements 4.2**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        analyzer = DataAnalyzer(output_dir=tmpdir)
        result = analyzer.analyze_price_trend(df)
        assert_chart_metadata_complete(result, "analyze_price_trend")


@settings(max_examples=100, deadline=None)
@given(df=price_dataframe_strategy())
def test_monthly_price_chart_metadata(df: pd.DataFrame):
    """属性测试：月度价格分析图表元数据完整性

    Feature: project-schedule, Property 7: 图表元数据完整性

    **Validates: Requirements 4.2**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        analyzer = DataAnalyzer(output_dir=tmpdir)
        result = analyzer.analyze_monthly_price(df)
        assert_chart_metadata_complete(result, "analyze_monthly_price")


@settings(max_examples=100, deadline=None)
@given(df=price_dataframe_strategy())
def test_regional_difference_chart_metadata(df: pd.DataFrame):
    """属性测试：地区差异分析图表元数据完整性

    Feature: project-schedule, Property 7: 图表元数据完整性

    **Validates: Requirements 4.2**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        analyzer = DataAnalyzer(output_dir=tmpdir)
        result = analyzer.analyze_regional_difference(df)
        assert_chart_metadata_complete(result, "analyze_regional_difference")


@settings(max_examples=100, deadline=None)
@given(df=weather_dataframe_strategy())
def test_weather_correlation_chart_metadata(df: pd.DataFrame):
    """属性测试：气象相关性分析图表元数据完整性

    Feature: project-schedule, Property 7: 图表元数据完整性

    **Validates: Requirements 4.2**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        analyzer = DataAnalyzer(output_dir=tmpdir)
        result = analyzer.analyze_weather_correlation(df)
        assert_chart_metadata_complete(result, "analyze_weather_correlation")


@settings(max_examples=100, deadline=None)
@given(df=price_dataframe_strategy())
def test_price_volatility_chart_metadata(df: pd.DataFrame):
    """属性测试：价格波动分析图表元数据完整性

    Feature: project-schedule, Property 7: 图表元数据完整性

    **Validates: Requirements 4.2**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        analyzer = DataAnalyzer(output_dir=tmpdir)
        result = analyzer.analyze_price_volatility(df)
        assert_chart_metadata_complete(result, "analyze_price_volatility")
