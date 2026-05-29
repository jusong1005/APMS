"""
属性测试：数据关联合并正确性

Feature: project-schedule, Property 4: 数据关联合并正确性

验证 DataCleaner.merge_data() 方法的正确性：
- 按 date 和 region 字段进行内连接合并后，结果集中每条记录应同时包含价格信息和气象信息
- 不存在 date+region 组合不匹配的记录
- 每行的 date+region 组合必须同时存在于两个原始 DataFrame 中

**Validates: Requirements 2.2**
"""

import pandas as pd
import numpy as np
from datetime import date, timedelta
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from backend.data_cleaner import DataCleaner


# ============================================================
# 策略定义
# ============================================================

# 地区名称池
REGION_POOL = ["山东", "河南", "四川", "广东", "江苏", "浙江", "湖北", "湖南", "北京", "上海"]

# 农产品名称池
PRODUCT_POOL = ["番茄", "玉米", "苹果", "黄瓜", "白菜", "土豆", "西瓜", "大蒜"]

# 生成非空地区集合的策略
regions_strategy = st.lists(
    st.sampled_from(REGION_POOL),
    min_size=1,
    max_size=5,
    unique=True,
)

# 生成日期列表的策略（限定合理范围）
dates_strategy = st.lists(
    st.dates(min_value=date(2020, 1, 1), max_value=date(2024, 12, 31)),
    min_size=1,
    max_size=10,
    unique=True,
)

# 价格值策略
price_strategy = st.floats(min_value=0.5, max_value=100.0, allow_nan=False, allow_infinity=False)

# 气象值策略
temperature_strategy = st.floats(min_value=-20.0, max_value=45.0, allow_nan=False, allow_infinity=False)
rainfall_strategy = st.floats(min_value=0.0, max_value=200.0, allow_nan=False, allow_infinity=False)
humidity_strategy = st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)


@st.composite
def price_dataframe_strategy(draw, regions, dates):
    """生成价格 DataFrame 的策略

    每个 (region, date) 组合生成一条或多条价格记录（不同产品）。
    """
    records = []
    # 从给定的 regions 和 dates 中选择子集
    selected_regions = draw(st.lists(
        st.sampled_from(regions),
        min_size=1,
        max_size=len(regions),
        unique=True,
    ))
    selected_dates = draw(st.lists(
        st.sampled_from(dates),
        min_size=1,
        max_size=len(dates),
        unique=True,
    ))

    for region in selected_regions:
        for d in selected_dates:
            product = draw(st.sampled_from(PRODUCT_POOL))
            avg_price = draw(price_strategy)
            record = {
                "product_name": product,
                "region": region,
                "date": d.strftime("%Y-%m-%d"),
                "average_price": round(avg_price, 2),
            }
            # 可选字段
            if draw(st.booleans()):
                record["highest_price"] = round(avg_price * draw(st.floats(min_value=1.0, max_value=1.5, allow_nan=False, allow_infinity=False)), 2)
            if draw(st.booleans()):
                record["lowest_price"] = round(avg_price * draw(st.floats(min_value=0.5, max_value=1.0, allow_nan=False, allow_infinity=False)), 2)
            if draw(st.booleans()):
                record["unit"] = "元/公斤"
            records.append(record)

    return pd.DataFrame(records)


@st.composite
def weather_dataframe_strategy(draw, regions, dates):
    """生成气象 DataFrame 的策略

    每个 (region, date) 组合生成一条气象记录。
    """
    records = []
    selected_regions = draw(st.lists(
        st.sampled_from(regions),
        min_size=1,
        max_size=len(regions),
        unique=True,
    ))
    selected_dates = draw(st.lists(
        st.sampled_from(dates),
        min_size=1,
        max_size=len(dates),
        unique=True,
    ))

    for region in selected_regions:
        for d in selected_dates:
            record = {
                "region": region,
                "date": d.strftime("%Y-%m-%d"),
                "average_temperature": round(draw(temperature_strategy), 2),
                "rainfall": round(draw(rainfall_strategy), 2),
                "humidity": round(draw(humidity_strategy), 2),
            }
            records.append(record)

    return pd.DataFrame(records)


@st.composite
def overlapping_price_weather_strategy(draw):
    """生成具有重叠 region+date 组合的价格和气象 DataFrame 对"""
    # 生成共享的地区和日期池
    all_regions = draw(regions_strategy)
    all_dates = draw(dates_strategy)

    price_df = draw(price_dataframe_strategy(all_regions, all_dates))
    weather_df = draw(weather_dataframe_strategy(all_regions, all_dates))

    return price_df, weather_df


# ============================================================
# 属性测试
# ============================================================

class TestDataMergeProperty:
    """Feature: project-schedule, Property 4: 数据关联合并正确性

    **Validates: Requirements 2.2**
    """

    def setup_method(self):
        self.cleaner = DataCleaner()

    @given(data=overlapping_price_weather_strategy())
    @settings(max_examples=100)
    def test_merged_rows_contain_both_price_and_weather_info(self, data):
        """合并后每条记录应同时包含价格信息和气象信息列。

        Feature: project-schedule, Property 4: 数据关联合并正确性
        **Validates: Requirements 2.2**
        """
        price_df, weather_df = data

        merged_df = self.cleaner.merge_data(price_df, weather_df)

        if len(merged_df) == 0:
            # 如果没有重叠的 date+region 组合，合并结果为空是正确的
            return

        # 验证合并后包含价格列
        assert "average_price" in merged_df.columns, (
            "合并结果缺少 average_price 列"
        )

        # 验证合并后包含气象列
        for weather_col in ["average_temperature", "rainfall", "humidity"]:
            assert weather_col in merged_df.columns, (
                f"合并结果缺少气象列: {weather_col}"
            )

        # 验证每行的价格字段不为空
        assert merged_df["average_price"].notna().all(), (
            "合并后存在 average_price 为空的记录"
        )

        # 验证每行的气象字段不为空
        for weather_col in ["average_temperature", "rainfall", "humidity"]:
            assert merged_df[weather_col].notna().all(), (
                f"合并后存在 {weather_col} 为空的记录"
            )

    @given(data=overlapping_price_weather_strategy())
    @settings(max_examples=100)
    def test_merged_date_region_exists_in_both_inputs(self, data):
        """合并后每行的 date+region 组合必须同时存在于两个原始 DataFrame 中。

        Feature: project-schedule, Property 4: 数据关联合并正确性
        **Validates: Requirements 2.2**
        """
        price_df, weather_df = data

        merged_df = self.cleaner.merge_data(price_df, weather_df)

        if len(merged_df) == 0:
            return

        # 获取原始 DataFrame 中的 date+region 组合集合
        # 注意：merge_data 内部会标准化日期格式，所以我们也需要标准化
        price_pairs = set(zip(
            pd.to_datetime(price_df["date"], format="mixed", errors="coerce").dt.strftime("%Y-%m-%d"),
            price_df["region"]
        ))
        weather_pairs = set(zip(
            pd.to_datetime(weather_df["date"], format="mixed", errors="coerce").dt.strftime("%Y-%m-%d"),
            weather_df["region"]
        ))

        # 验证合并结果中的每个 date+region 组合都存在于两个输入中
        for _, row in merged_df.iterrows():
            pair = (row["date"], row["region"])
            assert pair in price_pairs, (
                f"合并结果中的 date+region 组合 {pair} 不存在于价格数据中"
            )
            assert pair in weather_pairs, (
                f"合并结果中的 date+region 组合 {pair} 不存在于气象数据中"
            )

    @given(data=overlapping_price_weather_strategy())
    @settings(max_examples=100)
    def test_no_mismatched_date_region_in_merged_result(self, data):
        """合并结果中不应出现任何不在两个输入交集中的 date+region 组合。

        Feature: project-schedule, Property 4: 数据关联合并正确性
        **Validates: Requirements 2.2**
        """
        price_df, weather_df = data

        merged_df = self.cleaner.merge_data(price_df, weather_df)

        if len(merged_df) == 0:
            return

        # 计算两个输入的 date+region 交集
        price_pairs = set(zip(
            pd.to_datetime(price_df["date"], format="mixed", errors="coerce").dt.strftime("%Y-%m-%d"),
            price_df["region"]
        ))
        weather_pairs = set(zip(
            pd.to_datetime(weather_df["date"], format="mixed", errors="coerce").dt.strftime("%Y-%m-%d"),
            weather_df["region"]
        ))
        expected_intersection = price_pairs & weather_pairs

        # 验证合并结果中的所有 date+region 组合都在交集中
        merged_pairs = set(zip(merged_df["date"], merged_df["region"]))
        unexpected_pairs = merged_pairs - expected_intersection

        assert len(unexpected_pairs) == 0, (
            f"合并结果中存在不在两个输入交集中的 date+region 组合: {unexpected_pairs}"
        )

    @given(data=overlapping_price_weather_strategy())
    @settings(max_examples=100)
    def test_all_overlapping_pairs_present_in_merged_result(self, data):
        """两个输入中共有的 date+region 组合应全部出现在合并结果中。

        Feature: project-schedule, Property 4: 数据关联合并正确性
        **Validates: Requirements 2.2**
        """
        price_df, weather_df = data

        merged_df = self.cleaner.merge_data(price_df, weather_df)

        # 计算两个输入的 date+region 交集
        price_pairs = set(zip(
            pd.to_datetime(price_df["date"], format="mixed", errors="coerce").dt.strftime("%Y-%m-%d"),
            price_df["region"]
        ))
        weather_pairs = set(zip(
            pd.to_datetime(weather_df["date"], format="mixed", errors="coerce").dt.strftime("%Y-%m-%d"),
            weather_df["region"]
        ))
        expected_intersection = price_pairs & weather_pairs

        if len(merged_df) == 0:
            # 如果合并结果为空，交集也应为空
            assert len(expected_intersection) == 0, (
                f"交集非空但合并结果为空。交集: {expected_intersection}"
            )
            return

        # 验证交集中的所有 date+region 组合都出现在合并结果中
        merged_pairs = set(zip(merged_df["date"], merged_df["region"]))
        missing_pairs = expected_intersection - merged_pairs

        assert len(missing_pairs) == 0, (
            f"以下 date+region 组合存在于两个输入中但未出现在合并结果中: {missing_pairs}"
        )
