"""
工作量均衡验证模块 - 单元测试

验证 validate_workload 函数的两个约束：
1. 每位成员每周工作量不超过20工时
2. 任意两周之间的团队总工作量差异不超过较大值的30%

验证需求：7.2
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.workload_validator import (
    validate_workload,
    WorkloadValidationResult,
    WorkloadViolation,
    _normalize_schedule,
    _get_weekly_totals,
    _extract_week_number,
)


class TestValidateWorkloadMemberHoursConstraint:
    """测试约束1：每位成员每周≤20工时"""

    def test_all_members_within_limit(self):
        """所有成员每周工时均在限制内，应通过验证"""
        schedule = {"Alice": [15, 18, 16, 17], "Bob": [10, 12, 14, 11]}
        result = validate_workload(schedule)
        assert result.is_valid is True
        assert len(result.violations) == 0

    def test_member_exceeds_limit(self):
        """某成员某周超过20工时，应报告违规"""
        schedule = {"Alice": [25, 18, 16, 17]}
        result = validate_workload(schedule)
        assert result.is_valid is False
        assert any(v.constraint == "member_weekly_hours" for v in result.violations)

    def test_exactly_20_hours_is_valid(self):
        """恰好20工时应通过验证（≤20）"""
        schedule = {"Alice": [20, 20, 20, 20]}
        result = validate_workload(schedule)
        member_violations = [v for v in result.violations if v.constraint == "member_weekly_hours"]
        assert len(member_violations) == 0

    def test_slightly_over_20_hours(self):
        """20.1工时应报告违规"""
        schedule = {"Alice": [20.1, 15, 15, 15]}
        result = validate_workload(schedule)
        member_violations = [v for v in result.violations if v.constraint == "member_weekly_hours"]
        assert len(member_violations) == 1
        assert member_violations[0].details["member"] == "Alice"
        assert member_violations[0].details["week"] == 1

    def test_multiple_members_exceed(self):
        """多位成员超限，应分别报告"""
        schedule = {"Alice": [25, 15], "Bob": [15, 22]}
        result = validate_workload(schedule)
        member_violations = [v for v in result.violations if v.constraint == "member_weekly_hours"]
        assert len(member_violations) == 2

    def test_zero_hours_is_valid(self):
        """0工时应通过验证"""
        schedule = {"Alice": [0, 0, 0, 0]}
        result = validate_workload(schedule)
        member_violations = [v for v in result.violations if v.constraint == "member_weekly_hours"]
        assert len(member_violations) == 0

    def test_custom_max_hours(self):
        """使用自定义最大工时参数"""
        schedule = {"Alice": [15, 15, 15, 15]}
        result = validate_workload(schedule, max_weekly_hours_per_member=10.0)
        member_violations = [v for v in result.violations if v.constraint == "member_weekly_hours"]
        assert len(member_violations) == 4


class TestValidateWorkloadBalanceConstraint:
    """测试约束2：任意两周团队总工作量差异不超过较大值的30%"""

    def test_balanced_workload(self):
        """均衡的工作量分配应通过验证"""
        schedule = {"Alice": [15, 15, 15, 15], "Bob": [15, 15, 15, 15]}
        result = validate_workload(schedule)
        assert result.is_valid is True

    def test_unbalanced_workload(self):
        """不均衡的工作量分配应报告违规"""
        # week1=40, week2=10 -> diff=30, max=40, ratio=75% > 30%
        schedule = {"Alice": [20, 5, 20, 5], "Bob": [20, 5, 20, 5]}
        result = validate_workload(schedule)
        balance_violations = [v for v in result.violations if v.constraint == "weekly_balance"]
        assert len(balance_violations) > 0

    def test_exactly_30_percent_difference_is_valid(self):
        """恰好30%差异应通过验证（≤30%）"""
        # week1=30, week2=21 -> diff=9, max=30, ratio=0.30
        schedule = {"Alice": [15, 10.5], "Bob": [15, 10.5]}
        result = validate_workload(schedule)
        balance_violations = [v for v in result.violations if v.constraint == "weekly_balance"]
        assert len(balance_violations) == 0

    def test_slightly_over_30_percent(self):
        """略超30%差异应报告违规"""
        # week1=30, week2=20 -> diff=10, max=30, ratio=0.333 > 0.30
        schedule = {"Alice": [15, 10], "Bob": [15, 10]}
        result = validate_workload(schedule)
        balance_violations = [v for v in result.violations if v.constraint == "weekly_balance"]
        assert len(balance_violations) == 1

    def test_all_weeks_zero_is_valid(self):
        """所有周工时为0时应通过验证"""
        schedule = {"Alice": [0, 0, 0, 0]}
        result = validate_workload(schedule)
        assert result.is_valid is True

    def test_custom_ratio(self):
        """使用自定义差异比例参数"""
        # week1=20, week2=10 -> diff=10, max=20, ratio=0.50
        schedule = {"Alice": [20, 10]}
        # With 60% limit, should pass
        result = validate_workload(schedule, max_workload_difference_ratio=0.60)
        balance_violations = [v for v in result.violations if v.constraint == "weekly_balance"]
        assert len(balance_violations) == 0
        # With 40% limit, should fail
        result = validate_workload(schedule, max_workload_difference_ratio=0.40)
        balance_violations = [v for v in result.violations if v.constraint == "weekly_balance"]
        assert len(balance_violations) == 1


class TestInputFormats:
    """测试不同输入格式"""

    def test_dict_format(self):
        """Dict[str, List[float]] 格式"""
        schedule = {"Alice": [15, 18], "Bob": [12, 14]}
        result = validate_workload(schedule)
        assert isinstance(result, WorkloadValidationResult)

    def test_list_format(self):
        """List[dict] 格式"""
        schedule = [
            {"member": "Alice", "week": 1, "hours": 15.0},
            {"member": "Alice", "week": 2, "hours": 18.0},
            {"member": "Bob", "week": 1, "hours": 12.0},
            {"member": "Bob", "week": 2, "hours": 14.0},
        ]
        result = validate_workload(schedule)
        assert isinstance(result, WorkloadValidationResult)
        assert result.is_valid is True

    def test_list_format_accumulates_hours(self):
        """List格式中同一成员同一周多条记录应累加"""
        schedule = [
            {"member": "Alice", "week": 1, "hours": 10.0},
            {"member": "Alice", "week": 1, "hours": 12.0},  # total = 22 > 20
        ]
        result = validate_workload(schedule)
        assert result.is_valid is False
        member_violations = result.member_hours_violations
        assert len(member_violations) == 1
        assert member_violations[0].details["hours"] == 22.0

    def test_invalid_type_raises_error(self):
        """不支持的类型应抛出TypeError"""
        with pytest.raises(TypeError):
            validate_workload("invalid")

    def test_dict_of_dicts_format(self):
        """Dict[str, Dict[str, float]] 格式（week_N -> member -> hours）"""
        schedule = {
            "week_1": {"马一凡": 15, "盛晓宇": 18, "武殊宇": 16, "王羽菲": 14, "靳康琦": 17},
            "week_2": {"马一凡": 16, "盛晓宇": 17, "武殊宇": 18, "王羽菲": 15, "靳康琦": 16},
        }
        result = validate_workload(schedule)
        assert isinstance(result, WorkloadValidationResult)
        assert result.is_valid is True

    def test_dict_of_dicts_format_exceeds_hours(self):
        """Dict[str, Dict[str, float]] 格式中成员超时"""
        schedule = {
            "week_1": {"Alice": 25, "Bob": 15},
            "week_2": {"Alice": 15, "Bob": 15},
        }
        result = validate_workload(schedule)
        assert result.is_valid is False
        member_violations = result.member_hours_violations
        assert len(member_violations) == 1
        assert member_violations[0].details["member"] == "Alice"

    def test_dict_of_dicts_format_unbalanced(self):
        """Dict[str, Dict[str, float]] 格式中周间不均衡"""
        schedule = {
            "week_1": {"Alice": 20, "Bob": 20},  # total=40
            "week_2": {"Alice": 10, "Bob": 10},  # total=20, diff/max=50%>30%
        }
        result = validate_workload(schedule)
        assert result.is_valid is False
        balance_violations = result.balance_violations
        assert len(balance_violations) == 1


class TestNormalizeSchedule:
    """测试内部标准化函数"""

    def test_normalize_dict_format(self):
        """标准化Dict格式"""
        schedule = {"Alice": [10, 15, 20]}
        result = _normalize_schedule(schedule)
        assert result == {"Alice": {1: 10, 2: 15, 3: 20}}

    def test_normalize_list_format(self):
        """标准化List格式"""
        schedule = [
            {"member": "Alice", "week": 1, "hours": 10.0},
            {"member": "Bob", "week": 2, "hours": 15.0},
        ]
        result = _normalize_schedule(schedule)
        assert result == {"Alice": {1: 10.0}, "Bob": {2: 15.0}}

    def test_normalize_dict_of_dicts_format(self):
        """标准化Dict[str, Dict[str, float]]格式"""
        schedule = {
            "week_1": {"Alice": 10, "Bob": 12},
            "week_2": {"Alice": 15, "Bob": 18},
        }
        result = _normalize_schedule(schedule)
        assert result == {"Alice": {1: 10, 2: 15}, "Bob": {1: 12, 2: 18}}

    def test_normalize_empty_dict(self):
        """空字典应返回空结果"""
        result = _normalize_schedule({})
        assert result == {}


class TestExtractWeekNumber:
    """测试周编号提取函数"""

    def test_week_underscore_format(self):
        """week_N 格式"""
        assert _extract_week_number("week_1") == 1
        assert _extract_week_number("week_10") == 10

    def test_week_dash_format(self):
        """week-N 格式"""
        assert _extract_week_number("week-2") == 2

    def test_week_space_format(self):
        """week N 格式"""
        assert _extract_week_number("week 3") == 3

    def test_pure_number(self):
        """纯数字格式"""
        assert _extract_week_number("1") == 1
        assert _extract_week_number("4") == 4

    def test_case_insensitive(self):
        """大小写不敏感"""
        assert _extract_week_number("Week_1") == 1
        assert _extract_week_number("WEEK_2") == 2

    def test_invalid_format_raises_error(self):
        """无法提取周编号时应抛出ValueError"""
        with pytest.raises(ValueError):
            _extract_week_number("abc")


class TestGetWeeklyTotals:
    """测试周总工时计算"""

    def test_single_member(self):
        """单成员周总工时"""
        normalized = {"Alice": {1: 10, 2: 15, 3: 20}}
        totals = _get_weekly_totals(normalized)
        assert totals == {1: 10, 2: 15, 3: 20}

    def test_multiple_members(self):
        """多成员周总工时累加"""
        normalized = {"Alice": {1: 10, 2: 15}, "Bob": {1: 5, 2: 8}}
        totals = _get_weekly_totals(normalized)
        assert totals == {1: 15, 2: 23}


class TestViolationDetails:
    """测试违规详情信息"""

    def test_member_violation_details(self):
        """成员工时违规应包含完整详情"""
        schedule = {"Alice": [25, 15]}
        result = validate_workload(schedule)
        v = result.member_hours_violations[0]
        assert v.details["member"] == "Alice"
        assert v.details["week"] == 1
        assert v.details["hours"] == 25
        assert v.details["limit"] == 20.0

    def test_balance_violation_details(self):
        """均衡违规应包含完整详情"""
        # week1=30, week2=20 -> ratio=0.333
        schedule = {"Alice": [15, 10], "Bob": [15, 10]}
        result = validate_workload(schedule)
        v = result.balance_violations[0]
        assert v.details["week_a"] == 1
        assert v.details["week_b"] == 2
        assert v.details["total_a"] == 30.0
        assert v.details["total_b"] == 20.0
        assert abs(v.details["ratio"] - 1 / 3) < 0.01
