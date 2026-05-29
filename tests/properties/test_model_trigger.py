"""
属性测试：模型性能应急触发正确性

Feature: project-schedule, Property 9: 模型性能应急触发正确性

**Validates: Requirements 5.4**

对于任何模型评估指标集合（RMSE、R²、测试集均价），当RMSE超过测试集平均价格的30%
或R²低于0.5时，应急机制应被触发（要求增加ARIMA模型对比）；当两个条件均不满足时，不应触发。
"""

import sys
from pathlib import Path

from hypothesis import given, settings, assume
from hypothesis import strategies as st

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from backend.model_predictor import ModelPredictor
from models.schemas import ModelMetrics


@settings(max_examples=200)
@given(
    rmse=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    r_squared=st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    mean_price=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
)
def test_model_trigger_arima_property(rmse: float, r_squared: float, mean_price: float):
    """属性测试：模型性能应急触发正确性

    Feature: project-schedule, Property 9: 模型性能应急触发正确性

    **Validates: Requirements 5.4**

    对于随机生成的ModelMetrics（RMSE、R²、均价），验证should_trigger_arima()的返回值：
    - RMSE / mean_price > 0.30 OR R² < 0.5 → 应触发（返回True）
    - RMSE / mean_price <= 0.30 AND R² >= 0.5 → 不应触发（返回False）
    """
    # 确保mean_price不为0（避免除零）
    assume(mean_price != 0)

    # 构建ModelMetrics
    metrics = ModelMetrics(
        mae=rmse * 0.8,  # MAE不影响触发逻辑，设置合理值即可
        mse=rmse ** 2,
        rmse=rmse,
        r_squared=r_squared,
        test_set_mean_price=mean_price,
        training_records=100,
    )

    # 调用被测方法
    predictor = ModelPredictor()
    result = predictor.should_trigger_arima(metrics, test_mean_price=mean_price)

    # 计算预期结果
    rmse_ratio = rmse / mean_price
    should_trigger = rmse_ratio > 0.30 or r_squared < 0.5

    # 验证
    assert result == should_trigger, (
        f"should_trigger_arima() returned {result}, expected {should_trigger}. "
        f"rmse={rmse:.4f}, mean_price={mean_price:.4f}, "
        f"rmse_ratio={rmse_ratio:.4f} (threshold=0.30), "
        f"r_squared={r_squared:.4f} (threshold=0.50)"
    )
