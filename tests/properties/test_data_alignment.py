"""
属性测试：数据对齐验证

Feature: project-schedule, Property 2: 数据对齐验证

验证 DataCollector.validate_alignment() 方法的正确性：
- 气象数据应覆盖价格数据的所有地区和相同时间范围
- 当气象数据缺少价格数据中的某个地区或时间段时返回 False

**Validates: Requirements 1.2**
"""

import pandas as pd
from datetime import date, timedelta
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from backend.data_collector import DataCollector


# ============================================================
# 策略定义
# ============================================================

# 地区名称池
REGION_POOL = ["山东", "河南", "四川", "广东", "江苏", "浙江", "湖北", "湖南", "北京", "上海"]

# 生成非空地区集合的策略
regions_strategy = st.frozensets(
    st.sampled_from(REGION_POOL),
    min_size=1,
    max_size=5,
)

# 生成日期的策略（限定合理范围）
date_strategy = st.dates(
    min_value=date(2020, 1, 1),
    max_value=date(2025, 12, 31),
)


def build_df_with_regions_and_dates(regions, start_date, end_date):
    """构建包含 region 和 date 列的最小 DataFrame"""
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    records = []
    for region in regions:
        records.append({"region": region, "date": start_date.strftime("%Y-%m-%d")})
        if start_date != end_date:
            records.append({"region": region, "date": end_date.strftime("%Y-%m-%d")})
    return pd.DataFrame(records)


# ============================================================
# 属性测试
# ============================================================

class TestDataAlignmentProperty:
    """Feature: project-schedule, Property 2: 数据对齐验证

    **Validates: Requirements 1.2**
    """

    def setup_method(self):
        self.collector = DataCollector(seed=42)

    @given(
        price_regions=regions_strategy,
        weather_regions=regions_strategy,
        price_start=date_strategy,
        price_end=date_strategy,
        weather_start=date_strategy,
        weather_end=date_strategy,
    )
    @settings(max_examples=100)
    def test_alignment_region_and_time_coverage(
        self,
        price_regions,
        weather_regions,
        price_start,
        price_end,
        weather_start,
        weather_end,
    ):
        """对齐验证应在气象数据覆盖所有价格数据地区且时间范围完全覆盖时返回True，否则返回False。

        Feature: project-schedule, Property 2: 数据对齐验证
        **Validates: Requirements 1.2**
        """
        # 确保日期范围有效（start <= end）
        if price_start > price_end:
            price_start, price_end = price_end, price_start
        if weather_start > weather_end:
            weather_start, weather_end = weather_end, weather_start

        # 构建最小 DataFrame
        price_df = build_df_with_regions_and_dates(price_regions, price_start, price_end)
        weather_df = build_df_with_regions_and_dates(weather_regions, weather_start, weather_end)

        result = self.collector.validate_alignment(price_df, weather_df)

        # 计算预期结果
        regions_covered = price_regions.issubset(weather_regions)
        time_covered = (weather_start <= price_start) and (weather_end >= price_end)
        expected = regions_covered and time_covered

        assert result == expected, (
            f"validate_alignment returned {result}, expected {expected}. "
            f"price_regions={price_regions}, weather_regions={weather_regions}, "
            f"price_dates=[{price_start}, {price_end}], "
            f"weather_dates=[{weather_start}, {weather_end}], "
            f"regions_covered={regions_covered}, time_covered={time_covered}"
        )

    @given(
        shared_regions=regions_strategy,
        extra_weather_regions=regions_strategy,
        price_start=date_strategy,
        price_end=date_strategy,
        days_before=st.integers(min_value=0, max_value=30),
        days_after=st.integers(min_value=0, max_value=30),
    )
    @settings(max_examples=100)
    def test_alignment_true_when_weather_covers_price(
        self,
        shared_regions,
        extra_weather_regions,
        price_start,
        price_end,
        days_before,
        days_after,
    ):
        """当气象数据地区是价格数据地区的超集且时间范围完全覆盖时，应返回True。

        Feature: project-schedule, Property 2: 数据对齐验证
        **Validates: Requirements 1.2**
        """
        if price_start > price_end:
            price_start, price_end = price_end, price_start

        # 气象数据地区 = 价格数据地区 + 额外地区（超集）
        weather_regions = shared_regions | extra_weather_regions

        # 气象数据时间范围覆盖价格数据
        weather_start = price_start - timedelta(days=days_before)
        weather_end = price_end + timedelta(days=days_after)

        price_df = build_df_with_regions_and_dates(shared_regions, price_start, price_end)
        weather_df = build_df_with_regions_and_dates(weather_regions, weather_start, weather_end)

        result = self.collector.validate_alignment(price_df, weather_df)
        assert result is True, (
            f"Expected True when weather covers price data. "
            f"price_regions={shared_regions}, weather_regions={weather_regions}, "
            f"price_dates=[{price_start}, {price_end}], "
            f"weather_dates=[{weather_start}, {weather_end}]"
        )

    @given(
        price_regions=st.frozensets(
            st.sampled_from(REGION_POOL), min_size=2, max_size=5
        ),
        price_start=date_strategy,
        price_end=date_strategy,
    )
    @settings(max_examples=100)
    def test_alignment_false_when_weather_missing_region(
        self,
        price_regions,
        price_start,
        price_end,
    ):
        """当气象数据缺少价格数据中的某个地区时，应返回False。

        Feature: project-schedule, Property 2: 数据对齐验证
        **Validates: Requirements 1.2**
        """
        if price_start > price_end:
            price_start, price_end = price_end, price_start

        # 气象数据地区 = 价格数据地区去掉一个（不完全覆盖）
        price_regions_list = list(price_regions)
        weather_regions = frozenset(price_regions_list[:-1])  # 去掉最后一个地区

        price_df = build_df_with_regions_and_dates(price_regions, price_start, price_end)
        weather_df = build_df_with_regions_and_dates(weather_regions, price_start, price_end)

        result = self.collector.validate_alignment(price_df, weather_df)
        assert result is False, (
            f"Expected False when weather is missing region. "
            f"price_regions={price_regions}, weather_regions={weather_regions}"
        )

    @given(
        regions=regions_strategy,
        price_start=date_strategy,
        price_end=date_strategy,
        shrink_start_days=st.integers(min_value=1, max_value=30),
    )
    @settings(max_examples=100)
    def test_alignment_false_when_weather_time_starts_later(
        self,
        regions,
        price_start,
        price_end,
        shrink_start_days,
    ):
        """当气象数据开始日期晚于价格数据开始日期时，应返回False。

        Feature: project-schedule, Property 2: 数据对齐验证
        **Validates: Requirements 1.2**
        """
        if price_start > price_end:
            price_start, price_end = price_end, price_start

        # 确保价格数据有足够的时间跨度来缩减
        assume((price_end - price_start).days >= shrink_start_days)

        # 气象数据开始日期晚于价格数据
        weather_start = price_start + timedelta(days=shrink_start_days)
        weather_end = price_end

        price_df = build_df_with_regions_and_dates(regions, price_start, price_end)
        weather_df = build_df_with_regions_and_dates(regions, weather_start, weather_end)

        result = self.collector.validate_alignment(price_df, weather_df)
        assert result is False, (
            f"Expected False when weather starts later than price. "
            f"price_start={price_start}, weather_start={weather_start}"
        )

    @given(
        regions=regions_strategy,
        price_start=date_strategy,
        price_end=date_strategy,
        shrink_end_days=st.integers(min_value=1, max_value=30),
    )
    @settings(max_examples=100)
    def test_alignment_false_when_weather_time_ends_earlier(
        self,
        regions,
        price_start,
        price_end,
        shrink_end_days,
    ):
        """当气象数据结束日期早于价格数据结束日期时，应返回False。

        Feature: project-schedule, Property 2: 数据对齐验证
        **Validates: Requirements 1.2**
        """
        if price_start > price_end:
            price_start, price_end = price_end, price_start

        # 确保价格数据有足够的时间跨度来缩减
        assume((price_end - price_start).days >= shrink_end_days)

        # 气象数据结束日期早于价格数据
        weather_start = price_start
        weather_end = price_end - timedelta(days=shrink_end_days)

        price_df = build_df_with_regions_and_dates(regions, price_start, price_end)
        weather_df = build_df_with_regions_and_dates(regions, weather_start, weather_end)

        result = self.collector.validate_alignment(price_df, weather_df)
        assert result is False, (
            f"Expected False when weather ends earlier than price. "
            f"price_end={price_end}, weather_end={weather_end}"
        )
