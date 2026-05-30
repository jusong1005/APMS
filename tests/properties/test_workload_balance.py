"""
属性测试：工作量均衡约束

Feature: project-schedule, Property 10: 工作量均衡约束

**Validates: Requirements 7.2**

对于任何有效的任务分配方案，工作量验证函数应在每位成员每周工作量不超过20工时
且任意两周之间的团队总工作量差异不超过较大值的30%时返回通过；否则返回不通过。
"""

import sys
from pathlib import Path

from hypothesis import given, settings, assume
from hypothesis import strategies as st

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from backend.workload_validator import validate_workload


# 策略：生成随机的任务分配方案
# 成员数量 2-5，周数 2-4，每人每周工时 0.0-25.0
@st.composite
def schedule_strategy(draw):
    """生成随机的任务分配方案 {member_name: [week1_hours, week2_hours, ...]}"""
    num_members = draw(st.integers(min_value=2, max_value=5))
    num_weeks = draw(st.integers(min_value=2, max_value=4))

    schedule = {}
    for i in range(num_members):
        member_name = f"member_{i+1}"
        weekly_hours = [
            draw(st.floats(min_value=0.0, max_value=25.0, allow_nan=False, allow_infinity=False))
            for _ in range(num_weeks)
        ]
        schedule[member_name] = weekly_hours

    return schedule


def _compute_expected_validity(schedule: dict, max_hours: float = 20.0, max_ratio: float = 0.30) -> bool:
    """独立计算预期的验证结果

    Args:
        schedule: {member_name: [week1_hours, week2_hours, ...]}
        max_hours: 每位成员每周最大工时
        max_ratio: 任意两周团队总工时最大差异比例

    Returns:
        True 表示方案有效（通过验证），False 表示方案无效
    """
    # 约束1：检查是否有任何成员任何周超过 max_hours
    for member, weekly_hours in schedule.items():
        for hours in weekly_hours:
            if hours > max_hours:
                return False

    # 约束2：检查任意两周的团队总工时差异是否超过较大值的 max_ratio
    # 计算每周的团队总工时
    if not schedule:
        return True

    num_weeks = len(next(iter(schedule.values())))
    weekly_totals = []
    for week_idx in range(num_weeks):
        total = sum(hours_list[week_idx] for hours_list in schedule.values())
        weekly_totals.append(total)

    # 检查任意两周之间的差异
    for i in range(len(weekly_totals)):
        for j in range(i + 1, len(weekly_totals)):
            total_a = weekly_totals[i]
            total_b = weekly_totals[j]
            max_total = max(total_a, total_b)

            # 如果两周总工时都为0，差异为0，满足约束
            if max_total == 0:
                continue

            difference = abs(total_a - total_b)
            ratio = difference / max_total

            if ratio > max_ratio:
                return False

    return True


@settings(max_examples=200)
@given(schedule=schedule_strategy())
def test_workload_balance_property(schedule: dict):
    """属性测试：工作量均衡约束

    Feature: project-schedule, Property 10: 工作量均衡约束

    **Validates: Requirements 7.2**

    随机生成任务分配方案（工时0-25h），验证约束判定逻辑：
    - 每位成员每周工作量 ≤ 20h AND 任意两周团队总工时差异 ≤ 较大值的30% → is_valid=True
    - 否则 → is_valid=False
    """
    # 调用被测函数
    result = validate_workload(
        schedule,
        max_weekly_hours_per_member=20.0,
        max_workload_difference_ratio=0.30,
    )

    # 独立计算预期结果
    expected_valid = _compute_expected_validity(schedule, max_hours=20.0, max_ratio=0.30)

    # 验证结果一致
    assert result.is_valid == expected_valid, (
        f"validate_workload() returned is_valid={result.is_valid}, "
        f"expected {expected_valid}.\n"
        f"Schedule: {schedule}\n"
        f"Violations: {[(v.constraint, v.description) for v in result.violations]}"
    )
