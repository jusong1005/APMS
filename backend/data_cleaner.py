"""
数据清洗模块

实现农产品价格数据和气象数据的清洗、标准化、合并和质量验证功能。
清洗流程包括：缺失值处理、异常值修正、重复值删除、格式统一、数据合并和质量检查。

需求：2.1, 2.2, 2.3, 2.4, 2.5
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from config import (
    DATA_CLEANING,
    PROCESSED_DATA_DIR,
    PROCESSED_PRICE_CSV,
    PROCESSED_WEATHER_CSV,
    MERGED_DATA_CSV,
    RAW_PRICE_CSV,
    RAW_WEATHER_CSV,
)
from models.schemas import CleaningReport, QualityResult


class DataCleaner:
    """数据清洗与标准化处理模块

    负责对原始采集数据执行完整的清洗流程，包括：
    - 缺失值处理（均值/众数填充或字段删除）
    - 异常值修正（IQR方法）
    - 重复值删除
    - 格式标准化（日期、价格单位）
    - 数据关联合并
    - 质量验证

    清洗后输出 processed_price.csv 和 processed_weather.csv，
    并生成清洗报告。
    """

    # 价格数据中的数值字段（用于IQR异常值检测）
    PRICE_NUMERIC_COLUMNS = ["highest_price", "lowest_price", "average_price"]

    # 气象数据中的数值字段（用于IQR异常值检测）
    WEATHER_NUMERIC_COLUMNS = [
        "average_temperature",
        "highest_temperature",
        "lowest_temperature",
        "rainfall",
        "humidity",
        "sunshine_duration",
    ]

    def __init__(self):
        """初始化数据清洗器，从配置文件加载阈值参数"""
        self.missing_threshold = DATA_CLEANING["missing_threshold"]
        self.iqr_multiplier = DATA_CLEANING["iqr_multiplier"]
        self.quality_max_missing = DATA_CLEANING["quality_max_missing"]
        self.quality_max_duplicate = DATA_CLEANING["quality_max_duplicate"]
        self.date_format = DATA_CLEANING["date_format"]
        self.price_unit = DATA_CLEANING["price_unit"]

    def clean(self, df: pd.DataFrame, numeric_columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, CleaningReport]:
        """执行完整清洗流程，返回清洗后数据和清洗报告

        清洗步骤按顺序执行：
        1. 记录原始状态
        2. 处理缺失值
        3. 处理异常值
        4. 删除重复记录
        5. 标准化格式
        6. 生成清洗报告

        Args:
            df: 待清洗的原始DataFrame
            numeric_columns: 需要进行IQR异常值检测的数值列列表，
                           如果为None则自动检测

        Returns:
            (cleaned_df, report) 清洗后的DataFrame和清洗报告
        """
        original_records = len(df)
        df = df.copy()

        # 自动检测数值列（如果未指定）
        if numeric_columns is None:
            numeric_columns = self._detect_numeric_columns(df)

        # 步骤1：处理缺失值
        df, missing_filled, fields_dropped = self._handle_missing_values_with_stats(df)

        # 步骤2：处理异常值
        df, outliers_fixed = self._handle_outliers_with_stats(df, numeric_columns)

        # 步骤3：删除重复记录
        before_dedup = len(df)
        df = self.remove_duplicates(df)
        duplicates_removed = before_dedup - len(df)

        # 步骤4：标准化格式
        df = self.standardize_format(df)

        # 计算清洗后质量指标
        cleaned_records = len(df)
        missing_ratio_after = self._calculate_missing_ratio(df)
        duplicate_ratio_after = self._calculate_duplicate_ratio(df)

        # 生成清洗报告
        report = CleaningReport(
            original_records=original_records,
            cleaned_records=cleaned_records,
            missing_values_filled=missing_filled,
            fields_dropped=fields_dropped,
            outliers_fixed=outliers_fixed,
            duplicates_removed=duplicates_removed,
            missing_ratio_after=missing_ratio_after,
            duplicate_ratio_after=duplicate_ratio_after,
        )

        return df, report

    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """缺失值处理

        对每个字段检查缺失比例：
        - 缺失比例 < 50%：数值字段用均值填充，分类字段用众数填充
        - 缺失比例 >= 50%：删除该字段

        Args:
            df: 待处理的DataFrame

        Returns:
            处理后的DataFrame
        """
        df = df.copy()
        columns_to_drop = []

        for col in df.columns:
            missing_ratio = df[col].isna().sum() / len(df) if len(df) > 0 else 0

            if missing_ratio >= self.missing_threshold:
                # 缺失比例>=50%，删除字段
                columns_to_drop.append(col)
            elif missing_ratio > 0:
                # 缺失比例<50%，填充
                if pd.api.types.is_numeric_dtype(df[col]):
                    # 数值字段用均值填充
                    df[col] = df[col].fillna(df[col].mean())
                else:
                    # 分类字段用众数填充
                    mode_values = df[col].mode()
                    if len(mode_values) > 0:
                        df[col] = df[col].fillna(mode_values.iloc[0])

        # 删除缺失比例>=50%的字段
        if columns_to_drop:
            df = df.drop(columns=columns_to_drop)

        return df

    def handle_outliers(self, df: pd.DataFrame, numeric_columns: List[str]) -> pd.DataFrame:
        """异常值处理：对指定数值字段使用IQR方法修正为边界值

        对每个指定的数值列：
        - 计算Q1（25%分位数）和Q3（75%分位数）
        - 计算IQR = Q3 - Q1
        - 下界 = Q1 - 1.5 * IQR
        - 上界 = Q3 + 1.5 * IQR
        - 低于下界的值修正为下界值
        - 高于上界的值修正为上界值

        Args:
            df: 待处理的DataFrame
            numeric_columns: 需要进行IQR异常值检测的数值列列表

        Returns:
            处理后的DataFrame
        """
        df = df.copy()

        for col in numeric_columns:
            if col not in df.columns:
                continue
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue

            # 跳过全为NaN的列
            valid_data = df[col].dropna()
            if len(valid_data) == 0:
                continue

            q1 = valid_data.quantile(0.25)
            q3 = valid_data.quantile(0.75)
            iqr = q3 - q1

            lower_bound = q1 - self.iqr_multiplier * iqr
            upper_bound = q3 + self.iqr_multiplier * iqr

            # 修正异常值为边界值
            df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)

        return df

    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """重复值删除：基于全部字段完全相同的记录去重

        Args:
            df: 待处理的DataFrame

        Returns:
            去重后的DataFrame
        """
        return df.drop_duplicates().reset_index(drop=True)

    def standardize_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """字段格式统一

        - 日期字段统一为 YYYY-MM-DD 格式
        - 价格字段统一为 元/公斤 单位

        Args:
            df: 待处理的DataFrame

        Returns:
            格式统一后的DataFrame
        """
        df = df.copy()

        # 日期格式统一
        if "date" in df.columns:
            df["date"] = pd.to_datetime(
                df["date"], format="mixed", errors="coerce", dayfirst=False
            ).dt.strftime(self.date_format)

        # 价格单位统一
        if "unit" in df.columns:
            # 处理不同单位的转换
            for idx in df.index:
                unit = df.at[idx, "unit"]
                if pd.isna(unit):
                    df.at[idx, "unit"] = self.price_unit
                    continue

                unit_str = str(unit).strip()
                if unit_str == self.price_unit:
                    continue

                # 元/斤 -> 元/公斤（×2）
                if "元/斤" in unit_str:
                    for price_col in ["highest_price", "lowest_price", "average_price"]:
                        if price_col in df.columns and pd.notna(df.at[idx, price_col]):
                            df.at[idx, price_col] = round(
                                df.at[idx, price_col] * 2, 2
                            )
                    df.at[idx, "unit"] = self.price_unit

                # 元/吨 -> 元/公斤（÷1000）
                elif "元/吨" in unit_str:
                    for price_col in ["highest_price", "lowest_price", "average_price"]:
                        if price_col in df.columns and pd.notna(df.at[idx, price_col]):
                            df.at[idx, price_col] = round(
                                df.at[idx, price_col] / 1000, 2
                            )
                    df.at[idx, "unit"] = self.price_unit
                else:
                    # 未知单位，标记为标准单位（假设已是元/公斤）
                    df.at[idx, "unit"] = self.price_unit

        return df

    def merge_data(self, price_df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
        """按date和region字段关联合并价格和气象数据

        使用内连接（inner join），确保结果集中每条记录
        同时包含对应日期和地区的价格信息和气象信息。

        Args:
            price_df: 价格数据DataFrame（需包含date和region列）
            weather_df: 气象数据DataFrame（需包含date和region列）

        Returns:
            合并后的DataFrame
        """
        # 确保date列格式一致
        price_df = price_df.copy()
        weather_df = weather_df.copy()

        if "date" in price_df.columns:
            price_df["date"] = pd.to_datetime(
                price_df["date"], format="mixed", errors="coerce", dayfirst=False
            ).dt.strftime(self.date_format)
        if "date" in weather_df.columns:
            weather_df["date"] = pd.to_datetime(
                weather_df["date"], format="mixed", errors="coerce", dayfirst=False
            ).dt.strftime(self.date_format)

        # 内连接合并
        merged_df = pd.merge(
            price_df,
            weather_df,
            on=["date", "region"],
            how="inner",
        )

        return merged_df

    def validate_quality(
        self,
        df: pd.DataFrame,
        max_missing_ratio: Optional[float] = None,
        max_duplicate_ratio: Optional[float] = None,
    ) -> QualityResult:
        """验证清洗后数据质量是否达标

        当缺失值比例>20%或重复记录比例>10%时标记为不达标。

        Args:
            df: 待验证的DataFrame
            max_missing_ratio: 最大允许缺失比例，默认从配置读取（0.20）
            max_duplicate_ratio: 最大允许重复比例，默认从配置读取（0.10）

        Returns:
            QualityResult 数据质量检查结果
        """
        if max_missing_ratio is None:
            max_missing_ratio = self.quality_max_missing
        if max_duplicate_ratio is None:
            max_duplicate_ratio = self.quality_max_duplicate

        missing_ratio = self._calculate_missing_ratio(df)
        duplicate_ratio = self._calculate_duplicate_ratio(df)

        issues = []
        is_acceptable = True

        if missing_ratio > max_missing_ratio:
            is_acceptable = False
            issues.append(
                f"缺失值比例({missing_ratio:.2%})超过阈值({max_missing_ratio:.2%})"
            )

        if duplicate_ratio > max_duplicate_ratio:
            is_acceptable = False
            issues.append(
                f"重复记录比例({duplicate_ratio:.2%})超过阈值({max_duplicate_ratio:.2%})"
            )

        return QualityResult(
            is_acceptable=is_acceptable,
            missing_ratio=missing_ratio,
            duplicate_ratio=duplicate_ratio,
            issues=issues,
        )

    def run(self) -> dict:
        """执行完整的数据清洗流程

        按顺序执行：
        1. 读取原始CSV文件
        2. 分别清洗价格数据和气象数据
        3. 合并数据
        4. 验证质量
        5. 输出清洗后CSV文件
        6. 生成清洗报告

        Returns:
            包含清洗结果信息的字典
        """
        # 确保输出目录存在
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

        # 1. 读取原始数据
        print("[DataCleaner] 读取原始数据...")
        price_df = pd.read_csv(RAW_PRICE_CSV)
        weather_df = pd.read_csv(RAW_WEATHER_CSV)
        print(f"  价格数据: {len(price_df)} 条")
        print(f"  气象数据: {len(weather_df)} 条")

        # 2. 清洗价格数据
        print("[DataCleaner] 清洗价格数据...")
        cleaned_price_df, price_report = self.clean(
            price_df, numeric_columns=self.PRICE_NUMERIC_COLUMNS
        )
        print(f"  清洗后价格数据: {len(cleaned_price_df)} 条")

        # 3. 清洗气象数据
        print("[DataCleaner] 清洗气象数据...")
        cleaned_weather_df, weather_report = self.clean(
            weather_df, numeric_columns=self.WEATHER_NUMERIC_COLUMNS
        )
        print(f"  清洗后气象数据: {len(cleaned_weather_df)} 条")

        # 4. 合并数据
        print("[DataCleaner] 合并价格和气象数据...")
        merged_df = self.merge_data(cleaned_price_df, cleaned_weather_df)
        print(f"  合并后数据: {len(merged_df)} 条")

        # 5. 验证质量
        price_quality = self.validate_quality(cleaned_price_df)
        weather_quality = self.validate_quality(cleaned_weather_df)
        merged_quality = self.validate_quality(merged_df)

        print(f"[DataCleaner] 价格数据质量: {'达标' if price_quality.is_acceptable else '不达标'}")
        print(f"[DataCleaner] 气象数据质量: {'达标' if weather_quality.is_acceptable else '不达标'}")
        print(f"[DataCleaner] 合并数据质量: {'达标' if merged_quality.is_acceptable else '不达标'}")

        if not price_quality.is_acceptable:
            print(f"  问题: {'; '.join(price_quality.issues)}")
        if not weather_quality.is_acceptable:
            print(f"  问题: {'; '.join(weather_quality.issues)}")

        # 6. 输出清洗后CSV文件
        cleaned_price_df.to_csv(PROCESSED_PRICE_CSV, index=False, encoding="utf-8-sig")
        cleaned_weather_df.to_csv(PROCESSED_WEATHER_CSV, index=False, encoding="utf-8-sig")
        merged_df.to_csv(MERGED_DATA_CSV, index=False, encoding="utf-8-sig")

        print(f"[DataCleaner] 清洗后价格数据已保存: {PROCESSED_PRICE_CSV}")
        print(f"[DataCleaner] 清洗后气象数据已保存: {PROCESSED_WEATHER_CSV}")
        print(f"[DataCleaner] 合并数据已保存: {MERGED_DATA_CSV}")

        # 7. 生成清洗报告
        report_path = PROCESSED_DATA_DIR / "cleaning_report.md"
        self._generate_cleaning_report(
            price_report, weather_report, merged_quality, report_path
        )
        print(f"[DataCleaner] 清洗报告已生成: {report_path}")

        return {
            "price_cleaned_records": len(cleaned_price_df),
            "weather_cleaned_records": len(cleaned_weather_df),
            "merged_records": len(merged_df),
            "price_quality": price_quality.is_acceptable,
            "weather_quality": weather_quality.is_acceptable,
            "price_report": price_report,
            "weather_report": weather_report,
            "report_path": str(report_path),
        }

    # ================================================================
    # 私有辅助方法
    # ================================================================

    def _handle_missing_values_with_stats(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, int], List[str]]:
        """处理缺失值并返回统计信息

        Returns:
            (processed_df, missing_filled_dict, fields_dropped_list)
        """
        missing_filled: Dict[str, int] = {}
        fields_dropped: List[str] = []
        columns_to_drop = []

        for col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count == 0:
                continue

            missing_ratio = missing_count / len(df) if len(df) > 0 else 0

            if missing_ratio >= self.missing_threshold:
                # 缺失比例>=50%，删除字段
                columns_to_drop.append(col)
                fields_dropped.append(col)
            else:
                # 缺失比例<50%，填充
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].mean())
                else:
                    mode_values = df[col].mode()
                    if len(mode_values) > 0:
                        df[col] = df[col].fillna(mode_values.iloc[0])
                missing_filled[col] = int(missing_count)

        if columns_to_drop:
            df = df.drop(columns=columns_to_drop)

        return df, missing_filled, fields_dropped

    def _handle_outliers_with_stats(
        self, df: pd.DataFrame, numeric_columns: List[str]
    ) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """处理异常值并返回统计信息

        Returns:
            (processed_df, outliers_fixed_dict)
        """
        outliers_fixed: Dict[str, int] = {}

        for col in numeric_columns:
            if col not in df.columns:
                continue
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue

            valid_data = df[col].dropna()
            if len(valid_data) == 0:
                continue

            q1 = valid_data.quantile(0.25)
            q3 = valid_data.quantile(0.75)
            iqr = q3 - q1

            lower_bound = q1 - self.iqr_multiplier * iqr
            upper_bound = q3 + self.iqr_multiplier * iqr

            # 统计异常值数量
            outlier_count = int(
                ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            )

            if outlier_count > 0:
                df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
                outliers_fixed[col] = outlier_count

        return df, outliers_fixed

    def _detect_numeric_columns(self, df: pd.DataFrame) -> List[str]:
        """自动检测DataFrame中适合IQR处理的数值列

        排除id、日期等不适合IQR处理的列。
        """
        exclude_patterns = ["id", "date", "created_at"]
        numeric_cols = []

        for col in df.select_dtypes(include=[np.number]).columns:
            col_lower = col.lower()
            if not any(pattern in col_lower for pattern in exclude_patterns):
                numeric_cols.append(col)

        return numeric_cols

    def _calculate_missing_ratio(self, df: pd.DataFrame) -> float:
        """计算DataFrame的整体缺失值比例

        缺失比例 = 缺失单元格数 / 总单元格数
        """
        if df.empty:
            return 0.0
        total_cells = df.shape[0] * df.shape[1]
        if total_cells == 0:
            return 0.0
        missing_cells = df.isna().sum().sum()
        return float(missing_cells / total_cells)

    def _calculate_duplicate_ratio(self, df: pd.DataFrame) -> float:
        """计算DataFrame的重复记录比例

        重复比例 = 重复记录数 / 总记录数
        """
        if df.empty or len(df) == 0:
            return 0.0
        duplicate_count = df.duplicated().sum()
        return float(duplicate_count / len(df))

    def _generate_cleaning_report(
        self,
        price_report: CleaningReport,
        weather_report: CleaningReport,
        merged_quality: QualityResult,
        output_path: Path,
    ) -> None:
        """生成数据清洗报告文档"""
        report_content = f"""# 数据清洗报告

## 生成时间

{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. 价格数据清洗结果

### 1.1 基本统计

| 指标 | 数值 |
|------|------|
| 清洗前记录数 | {price_report.original_records} |
| 清洗后记录数 | {price_report.cleaned_records} |
| 删除重复记录数 | {price_report.duplicates_removed} |
| 清洗后缺失比例 | {price_report.missing_ratio_after:.4f} |
| 清洗后重复比例 | {price_report.duplicate_ratio_after:.4f} |

### 1.2 缺失值处理

"""
        if price_report.missing_values_filled:
            report_content += "| 字段 | 填充数量 |\n|------|----------|\n"
            for field, count in price_report.missing_values_filled.items():
                report_content += f"| {field} | {count} |\n"
        else:
            report_content += "无需填充的缺失值。\n"

        report_content += "\n### 1.3 删除的字段（缺失>=50%）\n\n"
        if price_report.fields_dropped:
            report_content += "、".join(price_report.fields_dropped) + "\n"
        else:
            report_content += "无删除字段。\n"

        report_content += "\n### 1.4 异常值修正\n\n"
        if price_report.outliers_fixed:
            report_content += "| 字段 | 修正数量 |\n|------|----------|\n"
            for field, count in price_report.outliers_fixed.items():
                report_content += f"| {field} | {count} |\n"
        else:
            report_content += "无异常值修正。\n"

        report_content += f"""
## 2. 气象数据清洗结果

### 2.1 基本统计

| 指标 | 数值 |
|------|------|
| 清洗前记录数 | {weather_report.original_records} |
| 清洗后记录数 | {weather_report.cleaned_records} |
| 删除重复记录数 | {weather_report.duplicates_removed} |
| 清洗后缺失比例 | {weather_report.missing_ratio_after:.4f} |
| 清洗后重复比例 | {weather_report.duplicate_ratio_after:.4f} |

### 2.2 缺失值处理

"""
        if weather_report.missing_values_filled:
            report_content += "| 字段 | 填充数量 |\n|------|----------|\n"
            for field, count in weather_report.missing_values_filled.items():
                report_content += f"| {field} | {count} |\n"
        else:
            report_content += "无需填充的缺失值。\n"

        report_content += "\n### 2.3 删除的字段（缺失>=50%）\n\n"
        if weather_report.fields_dropped:
            report_content += "、".join(weather_report.fields_dropped) + "\n"
        else:
            report_content += "无删除字段。\n"

        report_content += "\n### 2.4 异常值修正\n\n"
        if weather_report.outliers_fixed:
            report_content += "| 字段 | 修正数量 |\n|------|----------|\n"
            for field, count in weather_report.outliers_fixed.items():
                report_content += f"| {field} | {count} |\n"
        else:
            report_content += "无异常值修正。\n"

        report_content += f"""
## 3. 合并数据质量验证

| 指标 | 数值 | 阈值 | 状态 |
|------|------|------|------|
| 缺失值比例 | {merged_quality.missing_ratio:.4f} | ≤{self.quality_max_missing} | {'✓ 达标' if merged_quality.missing_ratio <= self.quality_max_missing else '✗ 不达标'} |
| 重复记录比例 | {merged_quality.duplicate_ratio:.4f} | ≤{self.quality_max_duplicate} | {'✓ 达标' if merged_quality.duplicate_ratio <= self.quality_max_duplicate else '✗ 不达标'} |

**总体质量判定**: {'✓ 达标' if merged_quality.is_acceptable else '✗ 不达标'}

"""
        if merged_quality.issues:
            report_content += "### 质量问题\n\n"
            for issue in merged_quality.issues:
                report_content += f"- {issue}\n"

        output_path.write_text(report_content, encoding="utf-8")


# 模块入口：直接运行时执行数据清洗
if __name__ == "__main__":
    cleaner = DataCleaner()
    result = cleaner.run()
    print("\n[DataCleaner] 数据清洗完成！")
    print(f"  价格数据: {result['price_cleaned_records']} 条")
    print(f"  气象数据: {result['weather_cleaned_records']} 条")
    print(f"  合并数据: {result['merged_records']} 条")
    print(f"  价格数据质量: {'达标' if result['price_quality'] else '不达标'}")
    print(f"  气象数据质量: {'达标' if result['weather_quality'] else '不达标'}")
