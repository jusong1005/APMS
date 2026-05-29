"""
属性测试：数据充分性验证

Feature: project-schedule, Property 1: 数据充分性验证

**Validates: Requirements 1.1**

对于任何数据集元信息（记录数、时间范围、农产品种类数、地区数），
数据充分性检查函数应在记录数少于1000条、或时间覆盖范围不足6个月、
或农产品种类少于3种、或地区少于2个时返回不通过；
当所有条件均满足时返回通过。
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from backend.data_collector import DataCollector


def build_dataframe(record_count: int, time_months: int, product_count: int, region_count: int) -> pd.DataFrame:
    """根据给定的元信息参数构建一个匹配的DataFrame。

    Args:
        record_count: 目标记录数
        time_months: 时间跨度（月）
        product_count: 农产品种类数
        region_count: 地区数

    Returns:
        构建的DataFrame，包含 product_name, region, date 列
    """
    if record_count == 0:
        return pd.DataFrame(columns=["product_name", "region", "date", "average_price"])

    # 生成产品名称列表
    all_products = [f"product_{i}" for i in range(product_count)]
    # 生成地区名称列表
    all_regions = [f"region_{i}" for i in range(region_count)]

    # 生成日期范围
    end_date = date(2024, 6, 30)
    if time_months > 0:
        start_date = end_date - timedelta(days=int(time_months * 30))
    else:
        start_date = end_date

    records = []
    for i in range(record_count):
        product = all_products[i % product_count]
        region = all_regions[i % region_count]

        # 在时间范围内均匀分布日期
        if time_months > 0 and record_count > 1:
            day_offset = int((end_date - start_date).days * (i / (record_count - 1)))
            record_date = start_date + timedelta(days=day_offset)
        else:
            record_date = end_date

        records.append({
            "product_name": product,
            "region": region,
            "date": record_date.strftime("%Y-%m-%d"),
            "average_price": 5.0,
        })

    return pd.DataFrame(records)


def expected_sufficiency(record_count: int, time_months: int, product_count: int, region_count: int) -> bool:
    """根据规则计算预期的充分性判定结果。

    规则：
    - 记录数 >= 1000
    - 时间跨度 >= 6 个月
    - 农产品种类 >= 3
    - 地区数 >= 2
    所有条件同时满足时返回 True，否则返回 False。
    """
    if record_count < 1000:
        return False
    if time_months < 6:
        return False
    if product_count < 3:
        return False
    if region_count < 2:
        return False
    return True


@settings(max_examples=200)
@given(
    record_count=st.integers(min_value=0, max_value=5000),
    time_months=st.integers(min_value=0, max_value=24),
    product_count=st.integers(min_value=1, max_value=10),
    region_count=st.integers(min_value=1, max_value=5),
)
def test_data_sufficiency_property(record_count: int, time_months: int, product_count: int, region_count: int):
    """属性测试：数据充分性验证

    Feature: project-schedule, Property 1: 数据充分性验证

    **Validates: Requirements 1.1**

    对于随机生成的数据集元信息，validate_sufficiency() 的返回值
    应与预期逻辑一致：
    - 记录数<1000 OR 时间<6月 OR 品种<3 OR 地区<2 → False
    - 所有条件均满足 → True
    """
    # 构建匹配参数的DataFrame
    df = build_dataframe(record_count, time_months, product_count, region_count)

    # 调用被测函数
    collector = DataCollector()
    result = collector.validate_sufficiency(df)

    # 计算预期结果
    expected = expected_sufficiency(record_count, time_months, product_count, region_count)

    # 验证
    assert result == expected, (
        f"validate_sufficiency() returned {result}, expected {expected}. "
        f"Params: records={record_count}, months={time_months}, "
        f"products={product_count}, regions={region_count}"
    )
