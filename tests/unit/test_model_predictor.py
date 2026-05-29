"""
模型预测模块单元测试

测试 ModelPredictor 类的核心功能：
- 特征工程
- 随机森林模型训练
- 模型评估
- 模型序列化保存和加载
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from backend.model_predictor import ModelPredictor
from models.schemas import ModelMetrics


@pytest.fixture
def predictor(tmp_path):
    """创建 ModelPredictor 实例，使用临时目录作为输出目录"""
    return ModelPredictor(output_dir=str(tmp_path / "charts"))


@pytest.fixture
def sample_df():
    """生成包含 date 和 region 列的示例 DataFrame"""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=200, freq="D")
    regions = ["北京", "上海", "广州"]
    data = {
        "date": np.random.choice(dates, 200),
        "region": np.random.choice(regions, 200),
        "average_price": np.random.uniform(2.0, 10.0, 200),
        "average_temperature": np.random.uniform(-5, 35, 200),
        "rainfall": np.random.uniform(0, 50, 200),
        "humidity": np.random.uniform(30, 90, 200),
    }
    return pd.DataFrame(data)


class TestEngineerFeatures:
    """测试特征工程功能"""

    def test_adds_time_features(self, predictor, sample_df):
        """测试添加时间特征列"""
        result = predictor.engineer_features(sample_df)
        assert "year" in result.columns
        assert "month" in result.columns
        assert "day_of_week" in result.columns
        assert "day_of_year" in result.columns

    def test_adds_season_feature(self, predictor, sample_df):
        """测试添加季节特征列"""
        result = predictor.engineer_features(sample_df)
        assert "season" in result.columns
        # 季节值应在 1-4 范围内
        assert result["season"].isin([1, 2, 3, 4]).all()

    def test_adds_region_encoded(self, predictor, sample_df):
        """测试添加地区编码特征"""
        result = predictor.engineer_features(sample_df)
        assert "region_encoded" in result.columns
        # 编码值应为非负整数
        assert (result["region_encoded"] >= 0).all()

    def test_no_region_column(self, predictor):
        """测试无 region 列时不添加 region_encoded"""
        df = pd.DataFrame({
            "date": pd.date_range("2023-01-01", periods=10),
            "average_price": np.random.uniform(2, 10, 10),
        })
        result = predictor.engineer_features(df)
        assert "region_encoded" not in result.columns

    def test_season_mapping_correct(self, predictor):
        """测试季节映射正确性"""
        # 春: 3,4,5  夏: 6,7,8  秋: 9,10,11  冬: 12,1,2
        assert predictor._get_season(3) == 1  # 春
        assert predictor._get_season(6) == 2  # 夏
        assert predictor._get_season(9) == 3  # 秋
        assert predictor._get_season(12) == 4  # 冬
        assert predictor._get_season(1) == 4  # 冬
        assert predictor._get_season(2) == 4  # 冬

    def test_does_not_modify_original(self, predictor, sample_df):
        """测试不修改原始 DataFrame"""
        original_cols = list(sample_df.columns)
        predictor.engineer_features(sample_df)
        assert list(sample_df.columns) == original_cols


class TestTrainRandomForest:
    """测试随机森林模型训练"""

    def test_train_success(self, predictor, sample_df):
        """测试正常训练成功"""
        df = predictor.engineer_features(sample_df)
        feature_cols = ["year", "month", "day_of_week", "day_of_year", "season",
                        "region_encoded", "average_temperature", "rainfall", "humidity"]
        X_train = df[feature_cols]
        y_train = df["average_price"]

        model = predictor.train_random_forest(X_train, y_train)
        assert model is not None
        assert hasattr(model, "predict")

    def test_raises_on_insufficient_data(self, predictor):
        """测试训练数据不足时抛出 ValueError"""
        X_train = pd.DataFrame({"a": range(50), "b": range(50)})
        y_train = pd.Series(range(50))

        with pytest.raises(ValueError, match="训练数据不足"):
            predictor.train_random_forest(X_train, y_train)

    def test_exactly_100_records(self, predictor):
        """测试恰好100条记录可以训练"""
        np.random.seed(42)
        X_train = pd.DataFrame({
            "a": np.random.randn(100),
            "b": np.random.randn(100),
        })
        y_train = pd.Series(np.random.randn(100))

        model = predictor.train_random_forest(X_train, y_train)
        assert model is not None


class TestEvaluateModel:
    """测试模型评估功能"""

    def test_returns_model_metrics(self, predictor, sample_df):
        """测试返回正确的 ModelMetrics 对象"""
        df = predictor.engineer_features(sample_df)
        feature_cols = ["year", "month", "day_of_week", "day_of_year", "season",
                        "region_encoded", "average_temperature", "rainfall", "humidity"]
        X = df[feature_cols]
        y = df["average_price"]

        # 训练模型
        model = predictor.train_random_forest(X, y)

        # 评估模型（使用训练集作为测试集，仅验证功能）
        metrics = predictor.evaluate_model(model, X, y)

        assert isinstance(metrics, ModelMetrics)
        assert metrics.mae >= 0
        assert metrics.mse >= 0
        assert metrics.rmse >= 0
        assert metrics.r_squared is not None
        assert metrics.test_set_mean_price is not None

    def test_generates_chart(self, predictor, sample_df):
        """测试生成对比图文件"""
        df = predictor.engineer_features(sample_df)
        feature_cols = ["year", "month", "day_of_week", "day_of_year", "season",
                        "region_encoded", "average_temperature", "rainfall", "humidity"]
        X = df[feature_cols]
        y = df["average_price"]

        model = predictor.train_random_forest(X, y)
        predictor.evaluate_model(model, X, y)

        chart_path = predictor.output_dir / "actual_vs_predicted.png"
        assert chart_path.exists()


class TestSaveLoadModel:
    """测试模型序列化保存和加载"""

    def test_save_and_load(self, predictor, sample_df, tmp_path):
        """测试保存后加载模型预测结果一致"""
        df = predictor.engineer_features(sample_df)
        feature_cols = ["year", "month", "day_of_week", "day_of_year", "season",
                        "region_encoded", "average_temperature", "rainfall", "humidity"]
        X = df[feature_cols]
        y = df["average_price"]

        model = predictor.train_random_forest(X, y)
        predictions_before = model.predict(X)

        # 保存模型
        model_path = str(tmp_path / "test_model.pkl")
        predictor.save_model(model, model_path)

        # 加载模型
        loaded_model = predictor.load_model(model_path)
        predictions_after = loaded_model.predict(X)

        # 预测结果应完全一致（允许浮点精度误差）
        np.testing.assert_array_almost_equal(predictions_before, predictions_after, decimal=10)

    def test_load_nonexistent_raises(self, predictor):
        """测试加载不存在的模型文件抛出 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            predictor.load_model("/nonexistent/path/model.pkl")

    def test_save_creates_directory(self, predictor, tmp_path):
        """测试保存时自动创建目录"""
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(n_estimators=5, random_state=42)
        model.fit([[1, 2], [3, 4], [5, 6]], [1, 2, 3])

        model_path = str(tmp_path / "subdir" / "model.pkl")
        predictor.save_model(model, model_path)
        assert Path(model_path).exists()


class TestShouldTriggerArima:
    """测试ARIMA应急触发逻辑"""

    def test_trigger_when_rmse_exceeds_30_percent(self, predictor):
        """测试RMSE超过均价30%时触发"""
        metrics = ModelMetrics(mae=3.0, mse=16.0, rmse=4.0, r_squared=0.80,
                               test_set_mean_price=10.0, training_records=100)
        # rmse/mean_price = 4.0/10.0 = 0.40 > 0.30
        assert predictor.should_trigger_arima(metrics, test_mean_price=10.0) is True

    def test_trigger_when_r2_below_05(self, predictor):
        """测试R²低于0.5时触发"""
        metrics = ModelMetrics(mae=1.0, mse=2.0, rmse=1.41, r_squared=0.40,
                               test_set_mean_price=10.0, training_records=100)
        # rmse/mean_price = 1.41/10.0 = 0.141 <= 0.30, but r² = 0.40 < 0.50
        assert predictor.should_trigger_arima(metrics, test_mean_price=10.0) is True

    def test_no_trigger_when_both_conditions_ok(self, predictor):
        """测试两个条件都满足时不触发"""
        metrics = ModelMetrics(mae=1.0, mse=2.0, rmse=2.0, r_squared=0.80,
                               test_set_mean_price=10.0, training_records=100)
        # rmse/mean_price = 2.0/10.0 = 0.20 <= 0.30, r² = 0.80 >= 0.50
        assert predictor.should_trigger_arima(metrics, test_mean_price=10.0) is False

    def test_trigger_both_conditions_fail(self, predictor):
        """测试两个条件都不满足时触发"""
        metrics = ModelMetrics(mae=5.0, mse=25.0, rmse=5.0, r_squared=0.30,
                               test_set_mean_price=10.0, training_records=100)
        # rmse/mean_price = 5.0/10.0 = 0.50 > 0.30 AND r² = 0.30 < 0.50
        assert predictor.should_trigger_arima(metrics, test_mean_price=10.0) is True

    def test_boundary_rmse_exactly_30_percent(self, predictor):
        """测试RMSE恰好等于均价30%时不触发（需要>30%）"""
        metrics = ModelMetrics(mae=2.0, mse=9.0, rmse=3.0, r_squared=0.80,
                               test_set_mean_price=10.0, training_records=100)
        # rmse/mean_price = 3.0/10.0 = 0.30, not > 0.30
        assert predictor.should_trigger_arima(metrics, test_mean_price=10.0) is False

    def test_boundary_r2_exactly_05(self, predictor):
        """测试R²恰好等于0.5时不触发（需要<0.5）"""
        metrics = ModelMetrics(mae=2.0, mse=4.0, rmse=2.0, r_squared=0.50,
                               test_set_mean_price=10.0, training_records=100)
        # rmse/mean_price = 2.0/10.0 = 0.20 <= 0.30, r² = 0.50 not < 0.50
        assert predictor.should_trigger_arima(metrics, test_mean_price=10.0) is False

    def test_no_trigger_when_mean_price_zero(self, predictor):
        """测试均价为0时返回False（避免除零）"""
        metrics = ModelMetrics(mae=1.0, mse=2.0, rmse=1.41, r_squared=0.30,
                               test_set_mean_price=0.0, training_records=100)
        assert predictor.should_trigger_arima(metrics, test_mean_price=0.0) is False

    def test_no_trigger_when_mean_price_none(self, predictor):
        """测试均价为None时返回False"""
        metrics = ModelMetrics(mae=1.0, mse=2.0, rmse=1.41, r_squared=0.30,
                               test_set_mean_price=None, training_records=100)
        assert predictor.should_trigger_arima(metrics, test_mean_price=None) is False

    def test_uses_metrics_mean_price_when_param_none(self, predictor):
        """测试当test_mean_price参数为None时使用metrics中的值"""
        metrics = ModelMetrics(mae=1.0, mse=2.0, rmse=5.0, r_squared=0.80,
                               test_set_mean_price=10.0, training_records=100)
        # rmse/mean_price = 5.0/10.0 = 0.50 > 0.30
        assert predictor.should_trigger_arima(metrics) is True

    def test_r_squared_none_only_checks_rmse(self, predictor):
        """测试R²为None时只检查RMSE条件"""
        metrics = ModelMetrics(mae=1.0, mse=2.0, rmse=2.0, r_squared=None,
                               test_set_mean_price=10.0, training_records=100)
        # rmse/mean_price = 2.0/10.0 = 0.20 <= 0.30, r² is None so not checked
        assert predictor.should_trigger_arima(metrics, test_mean_price=10.0) is False


class TestTrainArima:
    """测试ARIMA模型训练功能"""

    def test_train_arima_success(self, predictor):
        """测试正常训练ARIMA模型成功"""
        np.random.seed(42)
        # 生成一个简单的时间序列
        series = pd.Series(np.cumsum(np.random.randn(50)) + 100)
        result = predictor.train_arima(series)
        assert result is not None
        # ARIMA结果对象应有 forecast 方法
        assert hasattr(result, "forecast")

    def test_train_arima_custom_order(self, predictor):
        """测试使用自定义阶数训练ARIMA"""
        np.random.seed(42)
        series = pd.Series(np.cumsum(np.random.randn(50)) + 100)
        result = predictor.train_arima(series, order=(2, 1, 1))
        assert result is not None

    def test_train_arima_insufficient_data(self, predictor):
        """测试数据不足时抛出 ValueError"""
        series = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(ValueError, match="时间序列数据不足"):
            predictor.train_arima(series)

    def test_train_arima_exactly_10_points(self, predictor):
        """测试恰好10个数据点可以训练"""
        np.random.seed(42)
        series = pd.Series(np.cumsum(np.random.randn(10)) + 50)
        result = predictor.train_arima(series, order=(1, 0, 0))
        assert result is not None

    def test_train_arima_can_forecast(self, predictor):
        """测试训练后的模型可以进行预测"""
        np.random.seed(42)
        series = pd.Series(np.cumsum(np.random.randn(50)) + 100)
        result = predictor.train_arima(series)
        # 预测未来5个时间步
        forecast = result.forecast(steps=5)
        assert len(forecast) == 5
        assert all(np.isfinite(forecast))


class TestCompareModels:
    """测试模型对比功能"""

    def test_compare_models_output_format(self, predictor):
        """测试对比结果包含必要信息"""
        rf_metrics = ModelMetrics(mae=1.5, mse=3.0, rmse=1.73, r_squared=0.85,
                                  test_set_mean_price=10.0, training_records=100)
        arima_metrics = ModelMetrics(mae=2.0, mse=5.0, rmse=2.24, r_squared=0.70,
                                     test_set_mean_price=10.0, training_records=100)

        result = predictor.compare_models(rf_metrics, arima_metrics)

        assert "MAE" in result
        assert "MSE" in result
        assert "RMSE" in result
        assert "R²" in result
        assert "随机森林" in result
        assert "ARIMA" in result
        assert "结论" in result

    def test_compare_models_rf_better(self, predictor):
        """测试随机森林更优时的结论"""
        rf_metrics = ModelMetrics(mae=1.0, mse=2.0, rmse=1.41, r_squared=0.90,
                                  test_set_mean_price=10.0, training_records=100)
        arima_metrics = ModelMetrics(mae=2.0, mse=5.0, rmse=2.24, r_squared=0.70,
                                     test_set_mean_price=10.0, training_records=100)

        result = predictor.compare_models(rf_metrics, arima_metrics)
        assert "随机森林模型的RMSE更低" in result

    def test_compare_models_arima_better(self, predictor):
        """测试ARIMA更优时的结论"""
        rf_metrics = ModelMetrics(mae=3.0, mse=10.0, rmse=3.16, r_squared=0.40,
                                  test_set_mean_price=10.0, training_records=100)
        arima_metrics = ModelMetrics(mae=1.5, mse=3.0, rmse=1.73, r_squared=0.80,
                                     test_set_mean_price=10.0, training_records=100)

        result = predictor.compare_models(rf_metrics, arima_metrics)
        assert "ARIMA模型的RMSE更低" in result

    def test_compare_models_without_r_squared(self, predictor):
        """测试无R²时不输出R²行"""
        rf_metrics = ModelMetrics(mae=1.5, mse=3.0, rmse=1.73,
                                  test_set_mean_price=10.0, training_records=100)
        arima_metrics = ModelMetrics(mae=2.0, mse=5.0, rmse=2.24,
                                     test_set_mean_price=10.0, training_records=100)

        result = predictor.compare_models(rf_metrics, arima_metrics)
        assert "MAE" in result
        assert "RMSE" in result
        # R² should not appear since both are None
        assert "R²" not in result
