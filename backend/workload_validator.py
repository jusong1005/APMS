"""
工作量均衡验证模块

验证项目任务分配方案是否满足工作量均衡约束：
1. 每位成员每周工作量不超过 max_hours（默认20工时）
2. 任意两周之间的团队总工作量差异不超过较大值的 max_ratio（默认30%）

验证需求：7.2
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROJECT_CONFIG


# ============================================================
# 数据类
# ============================================================

@dataclass
class WorkloadViolation:
    """单条违规记录"""
    constraint: str       # "member_weekly_hours" 或 "weekly_balance"
    message: str          # 人类可读描述
    details: Dict         # 详细字段，方便断言


@dataclass
class WorkloadValidationResult:
    """validate_workload 的返回值"""
    is_valid: bool
    violations: List[WorkloadViolation] = field(default_factory=list)

    @property
    def member_hours_violations(self) -> List[WorkloadViolation]:
        return [v for v in self.violations if v.constraint == "member_weekly_hours"]

    @property
    def balance_violations(self) -> List[WorkloadViolation]:
        return [v for v in self.violations if v.constraint == "weekly_balance"]


# ============================================================
# 内部辅助函数（供测试直接导入）
# ============================================================

def _extract_week_number(key: str) -> int:
    """从字符串键中提取周编号（1-based）。

    支持：week_1, week-1, week 1, Week_1, WEEK_2, "1", "4" 等格式。
    无法提取时抛出 ValueError。
    """
    m = re.search(r"(\d+)", str(key))
    if m:
        return int(m.group(1))
    raise ValueError(f"无法从 '{key}' 中提取周编号")


def _normalize_schedule(
    schedule: Union[Dict, List]
) -> Dict[str, Dict[int, float]]:
    """将各种输入格式标准化为 {member: {week_no: hours}} 形式。

    支持格式：
    - Dict[str, List[float]]           {"Alice": [10, 15, 20]}
    - List[dict]                       [{"member": "Alice", "week": 1, "hours": 10.0}, ...]
    - Dict[str, Dict[str, float]]      {"week_1": {"Alice": 10}, "week_2": {"Alice": 15}}

    不支持的类型抛出 TypeError。
    """
    if isinstance(schedule, list):
        # 格式：[{"member": ..., "week": ..., "hours": ...}, ...]
        result: Dict[str, Dict[int, float]] = {}
        for item in schedule:
            member = item["member"]
            week = int(item["week"])
            hours = float(item["hours"])
            if member not in result:
                result[member] = {}
            result[member][week] = result[member].get(week, 0.0) + hours
        return result

    if not isinstance(schedule, dict):
        raise TypeError(f"不支持的类型：{type(schedule).__name__}")

    if not schedule:
        return {}

    # 判断格式：如果第一个值是 dict → Dict[week_key -> member_hours_dict]
    first_val = next(iter(schedule.values()))

    if isinstance(first_val, dict):
        # 格式：{"week_1": {"Alice": 10, "Bob": 12}, ...}
        result: Dict[str, Dict[int, float]] = {}
        for week_key, member_hours in schedule.items():
            week_no = _extract_week_number(week_key)
            for member, hours in member_hours.items():
                if member not in result:
                    result[member] = {}
                result[member][week_no] = float(hours)
        return result

    # 格式：{"Alice": [10, 15, 20], ...}
    result: Dict[str, Dict[int, float]] = {}
    for member, hours_list in schedule.items():
        if isinstance(hours_list, (list, tuple)):
            result[member] = {i + 1: float(h) for i, h in enumerate(hours_list)}
    return result


def _get_weekly_totals(
    normalized: Dict[str, Dict[int, float]]
) -> Dict[int, float]:
    """计算标准化排班中每周的团队总工时。

    Args:
        normalized: _normalize_schedule 返回的标准化格式

    Returns:
        {week_no: total_hours}
    """
    totals: Dict[int, float] = {}
    for member, week_hours in normalized.items():
        for week_no, hours in week_hours.items():
            totals[week_no] = totals.get(week_no, 0.0) + hours
    return totals


# ============================================================
# 主验证函数
# ============================================================

def validate_workload(
    schedule: Union[Dict, List],
    max_weekly_hours_per_member: Optional[float] = None,
    max_workload_difference_ratio: Optional[float] = None,
) -> WorkloadValidationResult:
    """综合验证完整排班方案的工作量均衡约束。

    验证需求：7.2

    Args:
        schedule: 任务分配方案，支持多种格式（见 _normalize_schedule）
        max_weekly_hours_per_member: 每人每周最大工时（默认从 PROJECT_CONFIG 读取：20.0）
        max_workload_difference_ratio: 两周差异上限（默认从 PROJECT_CONFIG 读取：0.30）

    Returns:
        WorkloadValidationResult
    """
    if max_weekly_hours_per_member is None:
        max_weekly_hours_per_member = PROJECT_CONFIG["max_weekly_hours_per_member"]
    if max_workload_difference_ratio is None:
        max_workload_difference_ratio = PROJECT_CONFIG["max_workload_difference_ratio"]

    # 标准化（可能抛出 TypeError / ValueError）
    normalized = _normalize_schedule(schedule)

    violations: List[WorkloadViolation] = []

    # ---- 约束1：成员每周工时 ≤ max_weekly_hours_per_member ----
    for member, week_hours in normalized.items():
        for week_no, hours in sorted(week_hours.items()):
            if hours > max_weekly_hours_per_member:
                violations.append(WorkloadViolation(
                    constraint="member_weekly_hours",
                    message=(
                        f"成员 '{member}' 第{week_no}周工时为 {hours:.1f}h，"
                        f"超过上限 {max_weekly_hours_per_member:.1f}h"
                    ),
                    details={
                        "member": member,
                        "week": week_no,
                        "hours": hours,
                        "limit": max_weekly_hours_per_member,
                    },
                ))

    # ---- 约束2：任意两周团队总工时差异 ≤ max_workload_difference_ratio ----
    weekly_totals = _get_weekly_totals(normalized)
    sorted_weeks = sorted(weekly_totals.keys())
    n = len(sorted_weeks)
    for i in range(n):
        for j in range(i + 1, n):
            wk_a = sorted_weeks[i]
            wk_b = sorted_weeks[j]
            total_a = weekly_totals[wk_a]
            total_b = weekly_totals[wk_b]
            max_total = max(total_a, total_b)
            if max_total == 0:
                continue
            ratio = abs(total_a - total_b) / max_total
            if ratio > max_workload_difference_ratio:
                violations.append(WorkloadViolation(
                    constraint="weekly_balance",
                    message=(
                        f"第{wk_a}周总工时({total_a:.1f}h)与"
                        f"第{wk_b}周总工时({total_b:.1f}h)的差异比例为"
                        f" {ratio:.2%}，超过上限 {max_workload_difference_ratio:.0%}"
                    ),
                    details={
                        "week_a": wk_a,
                        "week_b": wk_b,
                        "total_a": total_a,
                        "total_b": total_b,
                        "ratio": ratio,
                        "limit": max_workload_difference_ratio,
                    },
                ))

    return WorkloadValidationResult(
        is_valid=len(violations) == 0,
        violations=violations,
    )


# ============================================================
# 向后兼容的简单函数
# ============================================================

def validate_member_hours(
    member_hours: Dict[str, float],
    max_hours: float = 20.0,
) -> bool:
    """验证本周所有成员工时是否均不超过上限（向后兼容接口）。"""
    return all(h <= max_hours for h in member_hours.values())


def validate_weekly_balance(
    weekly_totals: List[float],
    max_ratio: float = 0.30,
) -> bool:
    """验证任意两周差异比例不超过 max_ratio（向后兼容接口）。"""
    n = len(weekly_totals)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = weekly_totals[i], weekly_totals[j]
            max_t = max(a, b)
            if max_t == 0:
                continue
            if abs(a - b) / max_t > max_ratio:
                return False
    return True
