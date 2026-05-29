"""
模型预测模块 - 随机森林价格预测模型训练与评估

实现农产品价格预测功能，包括：
- 特征工程：添加时间特征、季节特征和地区编码特征
- 随机森林回归模型训练（训练数据≥100条）
- 模型评估：计算MAE、MSE、RMSE指标，生成真实值与预测值对比图
- 模型序列化保存和加载
"""

import os
from pathlib import Path
from typing import Optional

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from statsmodels.tsa.arima.model import ARIMA

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from config import MODEL_CONFIG, RANDOM_FOREST_MODEL
from models.schemas import ModelMetrics

# 尝试设置中文字体
plt.rcParams["axes.unicode_minus"] = False
for font_name in ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei", "DejaVu Sans"]:
    if any(font_name in f.name for f in fm.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [font_name]
        break


class ModelPredictor:
    """价格预测模型训练与评估模块

    提供随机森林回归模型的特征工程、训练、评估和序列化功能。
    """

    def __init__(self, output_dir: Optional[str] = None):
        """初始化模型预测器

        Args:
            output_dir: 图表输出目录路径，默认为项目根目录下的 output/charts/
        """
        if output_dir is None:
            project_root = Path(__file__).parent.parent.resolve()
            self.output_dir = project_root / "output" / "charts"
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 从配置加载模型参数
        self.n_estimators = MODEL_CONFIG.get("n_estimators", 100)
        self.random_state = MODEL_CONFIG.get("random_state", 42)
        self.test_size = MODEL_CONFIG.get("test_size", 0.2)
        self.min_training_records = MODEL_CONFIG.get("min_training_records", 100)

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """特征工程：添加时间特征、季节特征和地区编码特征

        从 date 列提取时间特征，添加季节编码和地区标签编码。

        Args:
            df: 包含 date 列的 DataFrame，可选包含 region 列

        Returns:
            pd.DataFrame: 添加了新特征列的 DataFrame，包含：
                - year: 年份
                - month: 月份 (1-12)
                - day_of_week: 星期几 (0=周一, 6=周日)
                - day_of_year: 一年中的第几天 (1-366)
                - season: 季节 (1=春, 2=夏, 3=秋, 4=冬)
                - region_encoded: 地区标签编码（如有 region 列）
        """
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])

        # 时间特征
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        df["day_of_week"] = df["date"].dt.dayofweek
        df["day_of_year"] = df["date"].dt.dayofyear

        # 季节特征：春(3-5)=1, 夏(6-8)=2, 秋(9-11)=3, 冬(12,1,2)=4
        df["season"] = df["month"].apply(self._get_season)

        # 地区编码特征（标签编码）
        if "region" in df.columns:
            regions = sorted(df["region"].unique())
            region_map = {region: idx for idx, region in enumerate(regions)}
            df["region_encoded"] = df["region"].map(region_map)

        return df

    def train_random_forest(
        self, X_train: pd.DataFrame, y_train: pd.Series
    ) -> RandomForestRegressor:
        """训练随机森林回归模型

        使用 scikit-learn 的 RandomForestRegressor 训练价格预测模型。

        Args:
            X_train: 训练特征 DataFrame
            y_train: 训练目标 Series

        Returns:
            RandomForestRegressor: 训练好的随机森林模型

        Raises:
            ValueError: 当训练数据少于 min_training_records (100) 条时
        """
        if len(X_train) < self.min_training_records:
            raise ValueError(
                f"训练数据不足：需要至少{self.min_training_records}条记录，"
                f"当前仅有{len(X_train)}条。"
            )

        model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            n_jobs=-1,
        )
        model.fit(X_train, y_train)
        return model

    def evaluate_model(
        self,
        model,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> ModelMetrics:
        """评估模型性能

        计算 MAE、MSE、RMSE 和 R² 指标，并生成真实值与预测值对比图。

        Args:
            model: 训练好的模型（需支持 predict 方法）
            X_test: 测试特征 DataFrame
            y_test: 测试目标 Series

        Returns:
            ModelMetrics: 包含 MAE、MSE、RMSE、R² 等评估指标
        """
        y_pred = model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        r_squared = r2_score(y_test, y_pred)
        test_mean_price = float(y_test.mean())

        # 生成真实值与预测值对比图
        self._plot_actual_vs_predicted(y_test, y_pred, mae, rmse, r_squared)

        return ModelMetrics(
            mae=mae,
            mse=mse,
            rmse=rmse,
            r_squared=r_squared,
            test_set_mean_price=test_mean_price,
            training_records=len(X_test),
        )

    def save_model(self, model, filepath: Optional[str] = None) -> None:
        """序列化保存模型到文件

        使用 joblib 将训练好的模型保存为 .pkl 文件。

        Args:
            model: 要保存的模型对象
            filepath: 保存路径，默认使用配置中的 RANDOM_FOREST_MODEL 路径
        """
        if filepath is None:
            filepath = str(RANDOM_FOREST_MODEL)

        save_path = Path(filepath)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, filepath)

    def load_model(self, filepath: Optional[str] = None):
        """从文件加载序列化模型

        使用 joblib 从 .pkl 文件加载模型。

        Args:
            filepath: 模型文件路径，默认使用配置中的 RANDOM_FOREST_MODEL 路径

        Returns:
            加载的模型对象

        Raises:
            FileNotFoundError: 当模型文件不存在时
        """
        if filepath is None:
            filepath = str(RANDOM_FOREST_MODEL)

        if not Path(filepath).exists():
            raise FileNotFoundError(f"模型文件不存在：{filepath}")

        return joblib.load(filepath)

    def train_arima(self, series: pd.Series, order: tuple = (5, 1, 0)) -> object:
        """训练ARIMA时间序列模型

        使用 statsmodels 的 ARIMA 模型对价格时间序列进行拟合。

        Args:
            series: 时间序列数据（价格序列）
            order: ARIMA模型阶数 (p, d, q)，默认 (5, 1, 0)

        Returns:
            训练好的ARIMA模型结果对象（ARIMAResults）

        Raises:
            ValueError: 当时间序列数据不足时
        """
        if len(series) < 10:
            raise ValueError(
                f"时间序列数据不足：需要至少10个数据点，当前仅有{len(series)}个。"
            )

        model = ARIMA(series.values, order=order)
        result = model.fit()
        return result

    def compare_models(self, rf_metrics: ModelMetrics, arima_metrics: ModelMetrics) -> str:
        """对比随机森林和ARIMA模型的误差指标，输出对比结果

        当随机森林模型触发应急机制时，调用此方法输出两个模型的误差指标对比。

        Args:
            rf_metrics: 随机森林模型评估指标
            arima_metrics: ARIMA模型评估指标

        Returns:
            str: 格式化的模型对比结果字符串
        """
        comparison = (
            "=" * 60 + "\n"
            "模型误差指标对比结果\n"
            "=" * 60 + "\n"
            f"{'指标':<12}{'随机森林':<20}{'ARIMA':<20}\n"
            "-" * 60 + "\n"
            f"{'MAE':<12}{rf_metrics.mae:<20.4f}{arima_metrics.mae:<20.4f}\n"
            f"{'MSE':<12}{rf_metrics.mse:<20.4f}{arima_metrics.mse:<20.4f}\n"
            f"{'RMSE':<12}{rf_metrics.rmse:<20.4f}{arima_metrics.rmse:<20.4f}\n"
        )

        if rf_metrics.r_squared is not None and arima_metrics.r_squared is not None:
            comparison += (
                f"{'R²':<12}{rf_metrics.r_squared:<20.4f}{arima_metrics.r_squared:<20.4f}\n"
            )

        comparison += "-" * 60 + "\n"

        # 判断哪个模型更优（基于RMSE）
        if arima_metrics.rmse < rf_metrics.rmse:
            comparison += "结论：ARIMA模型的RMSE更低，建议采用ARIMA模型进行预测。\n"
        else:
            comparison += "结论：随机森林模型的RMSE更低，建议继续使用随机森林模型。\n"

        comparison += "=" * 60 + "\n"

        return comparison

    def should_trigger_arima(
        self, metrics: ModelMetrics, test_mean_price: Optional[float] = None
    ) -> bool:
        """判断是否需要触发ARIMA补充模型

        当随机森林模型的 RMSE 超过测试集平均价格的 30% 或 R² 低于 0.5 时，
        触发 ARIMA 模型作为补充对比。

        Args:
            metrics: 模型评估指标
            test_mean_price: 测试集平均价格，如为 None 则使用 metrics 中的值

        Returns:
            bool: 是否需要触发 ARIMA 模型
        """
        if test_mean_price is None:
            test_mean_price = metrics.test_set_mean_price

        if test_mean_price is None or test_mean_price == 0:
            return False

        rmse_ratio = metrics.rmse / test_mean_price
        arima_trigger_rmse = MODEL_CONFIG.get("arima_trigger_rmse_ratio", 0.30)
        arima_trigger_r2 = MODEL_CONFIG.get("arima_trigger_r2_threshold", 0.50)

        # RMSE超过均价30%或R²低于0.5时触发
        if rmse_ratio > arima_trigger_rmse:
            return True
        if metrics.r_squared is not None and metrics.r_squared < arima_trigger_r2:
            return True

        return False

    def _plot_actual_vs_predicted(
        self,
        y_test: pd.Series,
        y_pred: np.ndarray,
        mae: float,
        rmse: float,
        r_squared: float,
    ) -> str:
        """生成真实值与预测值对比图

        Args:
            y_test: 真实值
            y_pred: 预测值
            mae: 平均绝对误差
            rmse: 均方根误差
            r_squared: R²决定系数

        Returns:
            str: 图表文件保存路径
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # 子图1：散点图 - 真实值 vs 预测值
        ax1 = axes[0]
        ax1.scatter(y_test, y_pred, alpha=0.5, s=20, color="#409eff")
        # 绘制理想对角线
        min_val = min(y_test.min(), y_pred.min())
        max_val = max(y_test.max(), y_pred.max())
        ax1.plot(
            [min_val, max_val], [min_val, max_val],
            "r--", linewidth=1.5, label="理想预测线",
        )
        ax1.set_title("真实值 vs 预测值散点图")
        ax1.set_xlabel("真实价格（元/公斤）")
        ax1.set_ylabel("预测价格（元/公斤）")
        ax1.legend(loc="upper left")
        ax1.grid(True, alpha=0.3)

        # 添加指标文本
        metrics_text = f"MAE: {mae:.4f}\nRMSE: {rmse:.4f}\nR2: {r_squared:.4f}"
        ax1.text(
            0.95, 0.05, metrics_text,
            transform=ax1.transAxes, fontsize=9,
            verticalalignment="bottom", horizontalalignment="right",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )

        # 子图2：残差图
        ax2 = axes[1]
        residuals = np.array(y_test) - y_pred
        ax2.scatter(y_pred, residuals, alpha=0.5, s=20, color="#7c3aed")
        ax2.axhline(y=0, color="r", linestyle="--", linewidth=1.5)
        ax2.set_title("残差分布图")
        ax2.set_xlabel("预测价格（元/公斤）")
        ax2.set_ylabel("残差（元/公斤）")
        ax2.grid(True, alpha=0.3)

        fig.suptitle("随机森林模型预测效果评估", fontsize=14, fontweight="bold")
        fig.tight_layout()

        # 添加数据来源说明
        fig.text(
            0.5, 0.01,
            "数据来源：农产品批发市场价格信息系统",
            ha="center", fontsize=8, style="italic",
        )

        chart_path = str(self.output_dir / "actual_vs_predicted.png")
        fig.savefig(chart_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        return chart_path

    @staticmethod
    def _get_season(month: int) -> int:
        """根据月份返回季节编码

        Args:
            month: 月份 (1-12)

        Returns:
            int: 季节编码 (1=春, 2=夏, 3=秋, 4=冬)
        """
        if month in (3, 4, 5):
            return 1  # 春
        elif month in (6, 7, 8):
            return 2  # 夏
        elif month in (9, 10, 11):
            return 3  # 秋
        else:
            return 4  # 冬
