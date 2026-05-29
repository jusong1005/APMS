"""
属性测试：数据导入一致性

Feature: project-schedule, Property 6: 数据导入一致性

**Validates: Requirements 3.2**

对于任何CSV数据文件和对应的MySQL表，导入完成后MySQL表的记录数应与CSV文件的数据行数完全一致。
使用SQLite作为测试数据库（降级方案），验证导入后记录数与DataFrame行数一致。
"""

import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from backend.db_importer import DBImporter


# ============================================================
# 数据生成策略
# ============================================================

# 用于生成产品名称的策略
product_names = st.sampled_from(["番茄", "玉米", "苹果", "白菜", "土豆", "黄瓜", "西瓜", "大蒜"])
product_categories = st.sampled_from(["蔬菜", "水果", "粮食", "经济作物"])
market_names = st.sampled_from(["北京新发地", "上海江桥", "广州江南", "成都龙泉驿", "武汉白沙洲"])
regions = st.sampled_from(["北京", "上海", "广州", "成都", "武汉", "西安", "杭州"])
weather_conditions = st.sampled_from(["晴", "多云", "阴", "小雨", "大雨", "雪"])


@st.composite
def price_dataframes(draw, min_rows=1, max_rows=500):
    """生成随机价格数据DataFrame的策略。

    生成包含 product_name, product_category, market_name, region, date, average_price 等列的DataFrame。
    行数在 min_rows 到 max_rows 之间随机。
    """
    n_rows = draw(st.integers(min_value=min_rows, max_value=max_rows))

    records = []
    base_date = date(2024, 1, 1)

    for i in range(n_rows):
        day_offset = draw(st.integers(min_value=0, max_value=180))
        record_date = base_date + timedelta(days=day_offset)
        avg_price = draw(st.floats(min_value=0.5, max_value=50.0, allow_nan=False, allow_infinity=False))

        records.append({
            "product_name": draw(product_names),
            "product_category": draw(product_categories),
            "market_name": draw(market_names),
            "region": draw(regions),
            "date": record_date.strftime("%Y-%m-%d"),
            "average_price": round(avg_price, 2),
        })

    return pd.DataFrame(records)


@st.composite
def weather_dataframes(draw, min_rows=1, max_rows=500):
    """生成随机气象数据DataFrame的策略。

    生成包含 region, date, average_temperature, rainfall, humidity 等列的DataFrame。
    行数在 min_rows 到 max_rows 之间随机。
    """
    n_rows = draw(st.integers(min_value=min_rows, max_value=max_rows))

    records = []
    base_date = date(2024, 1, 1)

    for i in range(n_rows):
        day_offset = draw(st.integers(min_value=0, max_value=180))
        record_date = base_date + timedelta(days=day_offset)
        avg_temp = draw(st.floats(min_value=-10.0, max_value=40.0, allow_nan=False, allow_infinity=False))
        rainfall = draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
        humidity = draw(st.floats(min_value=20.0, max_value=100.0, allow_nan=False, allow_infinity=False))

        records.append({
            "region": draw(regions),
            "date": record_date.strftime("%Y-%m-%d"),
            "average_temperature": round(avg_temp, 2),
            "rainfall": round(rainfall, 2),
            "humidity": round(humidity, 2),
        })

    return pd.DataFrame(records)


# ============================================================
# 属性测试
# ============================================================


@settings(max_examples=100)
@given(price_df=price_dataframes(min_rows=1, max_rows=500))
def test_price_import_consistency(price_df: pd.DataFrame):
    """属性测试：价格数据导入一致性

    Feature: project-schedule, Property 6: 数据导入一致性

    **Validates: Requirements 3.2**

    对于随机生成的价格数据DataFrame，导入SQLite后，
    表中的记录数应与DataFrame的行数完全一致。
    """
    # 创建临时SQLite数据库（每次迭代独立）
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = str(Path(tmp_dir) / "test_price.db")
        connection_string = f"sqlite:///{db_path}"

        importer = DBImporter(connection_string)
        importer.create_tables()

        try:
            # 导入价格数据
            expected_count = len(price_df)
            imported_count = importer.import_price_data(price_df)

            # 验证导入返回值与DataFrame行数一致
            assert imported_count == expected_count, (
                f"import_price_data() returned {imported_count}, "
                f"expected {expected_count} (DataFrame rows)"
            )

            # 验证数据库中实际记录数与预期一致
            assert importer.verify_import("price_data", expected_count), (
                f"verify_import() failed: table record count does not match "
                f"expected {expected_count}"
            )
        finally:
            importer.close()


@settings(max_examples=100)
@given(weather_df=weather_dataframes(min_rows=1, max_rows=500))
def test_weather_import_consistency(weather_df: pd.DataFrame):
    """属性测试：气象数据导入一致性

    Feature: project-schedule, Property 6: 数据导入一致性

    **Validates: Requirements 3.2**

    对于随机生成的气象数据DataFrame，导入SQLite后，
    表中的记录数应与DataFrame的行数完全一致。
    """
    # 创建临时SQLite数据库（每次迭代独立）
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = str(Path(tmp_dir) / "test_weather.db")
        connection_string = f"sqlite:///{db_path}"

        importer = DBImporter(connection_string)
        importer.create_tables()

        try:
            # 导入气象数据
            expected_count = len(weather_df)
            imported_count = importer.import_weather_data(weather_df)

            # 验证导入返回值与DataFrame行数一致
            assert imported_count == expected_count, (
                f"import_weather_data() returned {imported_count}, "
                f"expected {expected_count} (DataFrame rows)"
            )

            # 验证数据库中实际记录数与预期一致
            assert importer.verify_import("weather_data", expected_count), (
                f"verify_import() failed: table record count does not match "
                f"expected {expected_count}"
            )
        finally:
            importer.close()
