"""
属性测试：清洗后数据质量阈值判定

Feature: project-schedule, Property 5: 清洗后数据质量阈值判定

**Validates: Requirements 2.5**

对于任何清洗后的数据集质量指标，当缺失值比例超过20%或重复记录比例超过10%时，
质量检查应返回不达标；当两个条件均不超过阈值时，返回达标。
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


def build_dataframe_with_ratios(
    n_rows: int, n_cols: int, target_missing_ratio: float, target_duplicate_ratio: float
) -> pd.DataFrame:
    """构建一个具有近似目标缺失比例和重复比例的DataFrame。

    策略：
    1. 先创建 unique_rows 行唯一数据
    2. 再添加 duplicate_rows 行重复数据以达到目标重复比例
    3. 在所有数据中注入 NaN 以达到目标缺失比例

    Args:
        n_rows: 总行数（唯一行 + 重复行）
        n_cols: 列数
        target_missing_ratio: 目标缺失值比例 (0.0 - 1.0)
        target_duplicate_ratio: 目标重复记录比例 (0.0 - 1.0)

    Returns:
        构建的DataFrame
    """
    # 计算重复行数：duplicate_ratio = duplicate_count / total_rows
    duplicate_rows = int(round(n_rows * target_duplicate_ratio))
    unique_rows = n_rows - duplicate_rows

    # 确保至少有1行唯一数据用于复制
    if unique_rows < 1:
        unique_rows = 1
        duplicate_rows = n_rows - 1

    # 生成唯一行数据（使用不同的值确保唯一性）
    data = {}
    for col_idx in range(n_cols):
        col_name = f"col_{col_idx}"
        # 每列使用不同的基数确保行间唯一
        data[col_name] = [float(row_idx * n_cols + col_idx + 1) for row_idx in range(unique_rows)]

    df = pd.DataFrame(data)

    # 添加重复行（复制第一行）
    if duplicate_rows > 0 and len(df) > 0:
        first_row = df.iloc[[0]]
        duplicates = pd.concat([first_row] * duplicate_rows, ignore_index=True)
        df = pd.concat([df, duplicates], ignore_index=True)

    # 注入缺失值以达到目标缺失比例
    total_cells = df.shape[0] * df.shape[1]
    target_missing_cells = int(round(total_cells * target_missing_ratio))

    if target_missing_cells > 0 and total_cells > 0:
        # 随机选择单元格设为NaN
        # 使用确定性方式注入NaN以避免随机性导致的不稳定
        cells_set = 0
        for idx in range(total_cells):
            if cells_set >= target_missing_cells:
                break
            row = idx // n_cols
            col = idx % n_cols
            df.iat[row, col] = np.nan
            cells_set += 1

    return df


@settings(max_examples=200)
@given(
    target_missing_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    target_duplicate_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
def test_quality_threshold_property(target_missing_ratio: float, target_duplicate_ratio: float):
    """属性测试：清洗后数据质量阈值判定

    Feature: project-schedule, Property 5: 清洗后数据质量阈值判定

    **Validates: Requirements 2.5**

    对于随机生成的缺失比例和重复比例，validate_quality() 的返回值应满足：
    - missing_ratio > 0.20 OR duplicate_ratio > 0.10 → is_acceptable = False
    - missing_ratio <= 0.20 AND duplicate_ratio <= 0.10 → is_acceptable = True
    """
    # 使用固定大小的DataFrame以确保比例计算精确
    n_rows = 100
    n_cols = 5

    # 构建具有目标比例的DataFrame
    df = build_dataframe_with_ratios(n_rows, n_cols, target_missing_ratio, target_duplicate_ratio)

    # 调用被测函数
    cleaner = DataCleaner()
    result = cleaner.validate_quality(df)

    # 计算实际的缺失比例和重复比例（与validate_quality内部逻辑一致）
    actual_missing_ratio = result.missing_ratio
    actual_duplicate_ratio = result.duplicate_ratio

    # 根据实际比例计算预期结果
    # 规则：missing_ratio > 0.20 OR duplicate_ratio > 0.10 → 不达标
    expected_acceptable = not (actual_missing_ratio > 0.20 or actual_duplicate_ratio > 0.10)

    # 验证
    assert result.is_acceptable == expected_acceptable, (
        f"validate_quality() returned is_acceptable={result.is_acceptable}, "
        f"expected {expected_acceptable}. "
        f"actual_missing_ratio={actual_missing_ratio:.4f} (threshold=0.20), "
        f"actual_duplicate_ratio={actual_duplicate_ratio:.4f} (threshold=0.10)"
    )

    # 额外验证：当不达标时，issues列表应非空
    if not result.is_acceptable:
        assert len(result.issues) > 0, (
            f"Quality is not acceptable but issues list is empty. "
            f"missing_ratio={actual_missing_ratio:.4f}, "
            f"duplicate_ratio={actual_duplicate_ratio:.4f}"
        )

    # 额外验证：当达标时，issues列表应为空
    if result.is_acceptable:
        assert len(result.issues) == 0, (
            f"Quality is acceptable but issues list is not empty: {result.issues}. "
            f"missing_ratio={actual_missing_ratio:.4f}, "
            f"duplicate_ratio={actual_duplicate_ratio:.4f}"
        )
