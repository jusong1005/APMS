"""
属性测试：数据清洗规则正确性

Feature: project-schedule, Property 3: 数据清洗规则正确性

**Validates: Requirements 2.1, 2.3**

对于任何包含缺失值、异常值和重复记录的原始数据集，清洗函数应满足：
(a) 缺失比例低于50%的数值字段使用均值填充后无空值
(b) 缺失比例>=50%的字段被删除
(c) 价格和气象数值字段中超出IQR范围的值被修正为边界值
    （不超出Q1-1.5×IQR至Q3+1.5×IQR范围）
(d) 完全重复的记录被去除
(e) 清洗后数据集的所有必填字段无空值
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from hypothesis import given, settings, assume
from hypothesis import strategies as st

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from backend.data_cleaner import DataCleaner


# ============================================================
# 策略：生成含缺失值的数值列数据
# ============================================================

@st.composite
def numeric_column_with_missing(draw, min_rows=10, max_rows=50, missing_ratio_range=(0.0, 0.8)):
    """生成一个含有缺失值的数值列。

    Args:
        min_rows: 最小行数
        max_rows: 最大行数
        missing_ratio_range: 缺失比例范围 (min, max)

    Returns:
        (values_list, target_missing_ratio) - 值列表和目标缺失比例
    """
    n_rows = draw(st.integers(min_value=min_rows, max_value=max_rows))
    missing_ratio = draw(st.floats(
        min_value=missing_ratio_range[0],
        max_value=missing_ratio_range[1],
    ))
    n_missing = int(n_rows * missing_ratio)

    # 生成基础数值数据
    values = draw(st.lists(
        st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        min_size=n_rows,
        max_size=n_rows,
    ))

    # 随机将部分值设为NaN
    missing_indices = draw(st.lists(
        st.integers(min_value=0, max_value=n_rows - 1),
        min_size=n_missing,
        max_size=n_missing,
        unique=True,
    )) if n_missing > 0 and n_missing <= n_rows else []

    for idx in missing_indices:
        values[idx] = np.nan

    return values, missing_ratio


@st.composite
def dataframe_with_issues(draw):
    """生成一个含有缺失值、异常值和重复记录的DataFrame。

    生成的DataFrame包含：
    - 多个数值列（部分有缺失值，缺失比例各不相同）
    - 一些极端异常值
    - 一些完全重复的行

    Returns:
        (df, numeric_columns, expected_dropped_cols) 元组
    """
    n_rows = draw(st.integers(min_value=10, max_value=50))
    n_numeric_cols = draw(st.integers(min_value=2, max_value=4))

    data = {}
    numeric_columns = []
    expected_dropped_cols = []

    for i in range(n_numeric_cols):
        col_name = f"num_col_{i}"
        numeric_columns.append(col_name)

        # 决定这一列的缺失比例
        missing_ratio = draw(st.sampled_from([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]))

        n_missing = int(n_rows * missing_ratio)

        # 生成基础数值
        base_values = draw(st.lists(
            st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
            min_size=n_rows,
            max_size=n_rows,
        ))

        # 注入异常值（极大或极小的值）
        n_outliers = draw(st.integers(min_value=0, max_value=min(3, n_rows)))
        outlier_indices = draw(st.lists(
            st.integers(min_value=0, max_value=n_rows - 1),
            min_size=n_outliers,
            max_size=n_outliers,
            unique=True,
        )) if n_outliers > 0 else []

        for idx in outlier_indices:
            # 生成明显的异常值
            outlier_value = draw(st.sampled_from([-9999.0, 9999.0, -5000.0, 5000.0]))
            base_values[idx] = outlier_value

        # 注入缺失值
        available_indices = list(range(n_rows))
        if n_missing > 0 and n_missing <= n_rows:
            missing_indices = draw(st.lists(
                st.integers(min_value=0, max_value=n_rows - 1),
                min_size=n_missing,
                max_size=n_missing,
                unique=True,
            ))
            for idx in missing_indices:
                base_values[idx] = np.nan

        data[col_name] = base_values

        # 记录预期被删除的列（缺失比例>=50%）
        if missing_ratio >= 0.5:
            expected_dropped_cols.append(col_name)

    # 添加一个非数值列（用于测试不影响数值处理）
    categories = ["A", "B", "C", "D"]
    data["category"] = [categories[i % len(categories)] for i in range(n_rows)]

    df = pd.DataFrame(data)

    # 注入重复行
    n_duplicates = draw(st.integers(min_value=0, max_value=min(5, n_rows)))
    if n_duplicates > 0 and len(df) > 0:
        dup_indices = draw(st.lists(
            st.integers(min_value=0, max_value=len(df) - 1),
            min_size=n_duplicates,
            max_size=n_duplicates,
        ))
        dup_rows = df.iloc[dup_indices]
        df = pd.concat([df, dup_rows], ignore_index=True)

    return df, numeric_columns, expected_dropped_cols


# ============================================================
# 属性测试
# ============================================================

@settings(max_examples=100)
@given(data=dataframe_with_issues())
def test_data_cleaning_rules_property(data):
    """属性测试：数据清洗规则正确性

    Feature: project-schedule, Property 3: 数据清洗规则正确性

    **Validates: Requirements 2.1, 2.3**

    验证清洗函数对随机生成的含缺失值、异常值和重复记录的DataFrame
    正确执行以下规则：
    (a) 缺失比例<50%的数值字段填充后无空值
    (b) 缺失比例>=50%的字段被删除
    (c) 数值字段值在IQR边界范围内
    (d) 完全重复的记录被去除
    (e) 所有保留字段无空值
    """
    df, numeric_columns, _ = data

    # 跳过空DataFrame
    assume(len(df) > 0)

    cleaner = DataCleaner()

    # 执行清洗
    cleaned_df, report = cleaner.clean(df, numeric_columns=numeric_columns)

    # ============================================================
    # 验证 (a): 缺失比例<50%的数值字段填充后无空值
    # ============================================================
    for col in numeric_columns:
        actual_missing_ratio = df[col].isna().sum() / len(df) if len(df) > 0 else 0
        if actual_missing_ratio < 0.5:
            # 该列应该被保留且无空值
            if col in cleaned_df.columns:
                null_count = cleaned_df[col].isna().sum()
                assert null_count == 0, (
                    f"Column '{col}' had missing ratio {actual_missing_ratio:.4f} (<50%), "
                    f"but still has {null_count} null values after cleaning"
                )

    # ============================================================
    # 验证 (b): 缺失比例>=50%的字段被删除
    # ============================================================
    for col in df.columns:
        # 计算原始DataFrame中该列的实际缺失比例
        # 注意：重复行被添加后，缺失比例可能变化
        actual_missing_ratio = df[col].isna().sum() / len(df) if len(df) > 0 else 0
        if actual_missing_ratio >= 0.5:
            assert col not in cleaned_df.columns, (
                f"Column '{col}' had missing ratio {actual_missing_ratio:.4f} (>=50%), "
                f"but was not dropped from the cleaned DataFrame"
            )

    # ============================================================
    # 验证 (c): 数值字段值在IQR边界范围内
    # 验证方式：模拟清洗流程中的IQR计算步骤
    # 先对原始数据执行缺失值填充（与clean方法相同），
    # 然后计算填充后数据的IQR边界，验证清洗后的值在这些边界内
    # ============================================================
    # 模拟缺失值填充步骤（与clean方法一致）
    df_after_fill = cleaner.handle_missing_values(df.copy())

    for col in numeric_columns:
        if col not in cleaned_df.columns:
            continue  # 已被删除的列跳过
        if col not in df_after_fill.columns:
            continue  # 填充阶段已被删除

        valid_data = df_after_fill[col].dropna()
        if len(valid_data) == 0:
            continue

        # 计算填充后数据的IQR边界（这是clean方法中实际使用的边界）
        q1 = valid_data.quantile(0.25)
        q3 = valid_data.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        # 清洗后的数据应在这些边界内
        cleaned_values = cleaned_df[col].dropna()
        if len(cleaned_values) == 0:
            continue

        below_lower = (cleaned_values < lower_bound - 1e-10).sum()
        above_upper = (cleaned_values > upper_bound + 1e-10).sum()

        assert below_lower == 0 and above_upper == 0, (
            f"Column '{col}' has values outside IQR bounds after cleaning: "
            f"{below_lower} below lower bound ({lower_bound:.4f}), "
            f"{above_upper} above upper bound ({upper_bound:.4f})"
        )

    # ============================================================
    # 验证 (d): 完全重复的记录被去除
    # ============================================================
    duplicate_count = cleaned_df.duplicated().sum()
    assert duplicate_count == 0, (
        f"Cleaned DataFrame still has {duplicate_count} duplicate records"
    )

    # ============================================================
    # 验证 (e): 所有保留字段无空值
    # ============================================================
    for col in cleaned_df.columns:
        null_count = cleaned_df[col].isna().sum()
        assert null_count == 0, (
            f"Column '{col}' still has {null_count} null values after cleaning"
        )


@settings(max_examples=100)
@given(
    n_rows=st.integers(min_value=10, max_value=50),
    missing_ratio=st.floats(min_value=0.5, max_value=0.9),
)
def test_high_missing_ratio_columns_dropped(n_rows: int, missing_ratio: float):
    """属性测试：高缺失比例字段被删除

    Feature: project-schedule, Property 3: 数据清洗规则正确性

    **Validates: Requirements 2.1, 2.3**

    验证当数值字段缺失比例>=50%时，该字段在清洗后被删除。
    """
    # 计算实际缺失数量，确保实际比例 >= 0.5
    import math
    n_missing = math.ceil(n_rows * missing_ratio)
    n_missing = min(n_missing, n_rows)  # 不超过总行数
    # 确保实际缺失比例 >= 50%
    actual_ratio = n_missing / n_rows
    assume(actual_ratio >= 0.5)

    # 创建一个正常列和一个高缺失列
    normal_values = [float(i) for i in range(n_rows)]
    high_missing_values = [np.nan if i < n_missing else float(i) for i in range(n_rows)]

    df = pd.DataFrame({
        "normal_col": normal_values,
        "high_missing_col": high_missing_values,
        "category": ["A"] * n_rows,
    })

    cleaner = DataCleaner()
    cleaned_df, report = cleaner.clean(df, numeric_columns=["normal_col", "high_missing_col"])

    # 高缺失列应被删除
    assert "high_missing_col" not in cleaned_df.columns, (
        f"Column 'high_missing_col' with actual missing ratio {actual_ratio:.4f} was not dropped"
    )
    # 正常列应保留
    assert "normal_col" in cleaned_df.columns, (
        "Column 'normal_col' with no missing values was incorrectly dropped"
    )
    # 报告中应记录被删除的字段
    assert "high_missing_col" in report.fields_dropped, (
        f"'high_missing_col' not found in report.fields_dropped: {report.fields_dropped}"
    )


@settings(max_examples=100)
@given(
    n_rows=st.integers(min_value=10, max_value=50),
    n_duplicates=st.integers(min_value=1, max_value=10),
)
def test_duplicates_removed(n_rows: int, n_duplicates: int):
    """属性测试：重复记录被去除

    Feature: project-schedule, Property 3: 数据清洗规则正确性

    **Validates: Requirements 2.1, 2.3**

    验证完全重复的记录在清洗后被去除。
    """
    # 构建一个有重复行的DataFrame
    base_data = {
        "col_a": [float(i) for i in range(n_rows)],
        "col_b": [float(i * 2) for i in range(n_rows)],
        "category": [f"cat_{i % 3}" for i in range(n_rows)],
    }
    df = pd.DataFrame(base_data)

    # 添加重复行
    dup_indices = [i % n_rows for i in range(n_duplicates)]
    dup_rows = df.iloc[dup_indices]
    df_with_dups = pd.concat([df, dup_rows], ignore_index=True)

    cleaner = DataCleaner()
    cleaned_df, report = cleaner.clean(df_with_dups, numeric_columns=["col_a", "col_b"])

    # 清洗后不应有重复记录
    assert cleaned_df.duplicated().sum() == 0, (
        f"Cleaned DataFrame still has duplicates after cleaning"
    )
    # 报告中应记录删除的重复数
    assert report.duplicates_removed >= n_duplicates, (
        f"Expected at least {n_duplicates} duplicates removed, "
        f"but report shows {report.duplicates_removed}"
    )


@settings(max_examples=100)
@given(
    n_rows=st.integers(min_value=20, max_value=50),
    outlier_value=st.floats(min_value=5000.0, max_value=10000.0),
)
def test_outliers_clipped_to_iqr_bounds(n_rows: int, outlier_value: float):
    """属性测试：异常值被修正为IQR边界值

    Feature: project-schedule, Property 3: 数据清洗规则正确性

    **Validates: Requirements 2.1, 2.3**

    验证数值字段中超出IQR范围的值被修正为边界值。
    """
    # 构建一个有明显异常值的DataFrame
    # 正常值在1-100范围内，异常值远超此范围
    np.random.seed(42)
    normal_values = list(np.random.uniform(10.0, 50.0, size=n_rows - 2))
    # 添加一个极大异常值和一个极小异常值
    normal_values.append(outlier_value)
    normal_values.append(-outlier_value)

    df = pd.DataFrame({
        "price_col": normal_values,
        "category": ["A"] * len(normal_values),
    })

    cleaner = DataCleaner()
    cleaned_df, report = cleaner.clean(df, numeric_columns=["price_col"])

    # 计算清洗后数据的IQR边界
    valid_data = cleaned_df["price_col"].dropna()
    q1 = valid_data.quantile(0.25)
    q3 = valid_data.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    # 所有值应在IQR边界内
    assert (valid_data >= lower_bound).all(), (
        f"Some values are below lower bound {lower_bound:.2f}"
    )
    assert (valid_data <= upper_bound).all(), (
        f"Some values are above upper bound {upper_bound:.2f}"
    )
