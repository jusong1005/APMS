"""
属性测试：模型序列化往返

Feature: project-schedule, Property 8: 模型序列化往返

**Validates: Requirements 5.3**

对于任何训练完成的预测模型，序列化保存后再加载，
使用相同测试数据进行预测应产生完全相同的结果。
"""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from backend.model_predictor import ModelPredictor


# 策略：生成随机训练数据的行数（至少100行，因为ModelPredictor要求最少100条）
n_rows_strategy = st.integers(min_value=100, max_value=200)
# 策略：随机种子，用于可重现的数据生成
seed_strategy = st.integers(min_value=0, max_value=2**31 - 1)


def generate_training_data(n_rows: int, rng: np.random.Generator) -> tuple:
    """生成模拟农产品价格预测的训练数据

    生成包含 year, month, day_of_week, day_of_year, season,
    region_encoded, temperature, rainfall, humidity 等特征的 DataFrame，
    以及对应的 average_price 目标值。
    """
    df = pd.DataFrame({
        "year": rng.integers(2018, 2024, size=n_rows),
        "month": rng.integers(1, 13, size=n_rows),
        "day_of_week": rng.integers(0, 7, size=n_rows),
        "day_of_year": rng.integers(1, 367, size=n_rows),
        "season": rng.integers(1, 5, size=n_rows),
        "region_encoded": rng.integers(0, 5, size=n_rows),
        "temperature": rng.uniform(-10.0, 40.0, size=n_rows),
        "rainfall": rng.uniform(0.0, 200.0, size=n_rows),
        "humidity": rng.uniform(20.0, 100.0, size=n_rows),
    })

    # 目标值：模拟农产品价格（元/公斤）
    y = pd.Series(
        rng.uniform(1.0, 50.0, size=n_rows),
        name="average_price",
    )

    return df, y


@settings(max_examples=20, deadline=None)
@given(
    n_rows=n_rows_strategy,
    seed=seed_strategy,
)
def test_model_serialization_roundtrip(n_rows: int, seed: int):
    """属性测试：模型序列化往返

    Feature: project-schedule, Property 8: 模型序列化往返

    **Validates: Requirements 5.3**

    对于随机生成的训练数据，训练随机森林模型后：
    1. 使用 save_model 序列化保存
    2. 使用 load_model 反序列化加载
    3. 对相同测试数据进行预测
    4. 验证原始模型和加载后模型的预测结果完全一致
    """
    rng = np.random.default_rng(seed)

    # 生成随机训练特征数据（使用领域相关特征）
    X_train, y_train = generate_training_data(n_rows, rng)

    # 生成测试数据（用于预测对比）
    n_test = max(20, n_rows // 5)
    X_test, _ = generate_training_data(n_test, rng)

    # 初始化 ModelPredictor
    predictor = ModelPredictor()

    # 训练随机森林模型
    model = predictor.train_random_forest(X_train, y_train)

    # 使用原始模型进行预测
    predictions_original = model.predict(X_test)

    # 在临时目录中序列化保存和加载
    with tempfile.TemporaryDirectory() as tmp_dir:
        model_path = str(Path(tmp_dir) / "test_model.pkl")

        # 保存模型
        predictor.save_model(model, filepath=model_path)

        # 加载模型
        loaded_model = predictor.load_model(filepath=model_path)

    # 使用加载后的模型进行预测
    predictions_loaded = loaded_model.predict(X_test)

    # 验证预测结果完全一致
    # 使用 assert_array_almost_equal 验证序列化往返后预测一致性
    # 允许极小的浮点精度差异（1e-10），因为随机森林在聚合多棵树预测时
    # 可能因浮点运算顺序产生机器精度级别的差异
    np.testing.assert_allclose(
        predictions_original,
        predictions_loaded,
        rtol=0,
        atol=1e-10,
        err_msg=(
            f"模型序列化往返后预测结果不一致。"
            f"训练数据: {n_rows}行, 测试数据: {n_test}行, seed={seed}. "
            f"最大差异: {np.max(np.abs(predictions_original - predictions_loaded))}"
        ),
    )
