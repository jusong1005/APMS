"""
Flask后端REST API服务

提供以下接口：
- /api/overview: 数据集基本统计信息和数据量
- /api/price-trends: 价格趋势数据，支持按product和region参数筛选
- /api/weather-impact: 气象因素与价格的相关性矩阵数据
- /api/predictions: 预测结果对比数据和模型误差指标

通过 `python app.py` 启动，默认端口5000。
"""

import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

from config import (
    API_CONFIG,
    MERGED_DATA_CSV,
    PROCESSED_PRICE_CSV,
    PROCESSED_WEATHER_CSV,
    RANDOM_FOREST_MODEL,
)

app = Flask(__name__)

# 配置CORS，允许前端跨域请求
CORS(app, origins=API_CONFIG["cors_origins"])


def _load_price_data() -> pd.DataFrame:
    """加载处理后的价格数据"""
    if PROCESSED_PRICE_CSV.exists():
        return pd.read_csv(str(PROCESSED_PRICE_CSV))
    return pd.DataFrame()


def _load_weather_data() -> pd.DataFrame:
    """加载处理后的气象数据"""
    if PROCESSED_WEATHER_CSV.exists():
        return pd.read_csv(str(PROCESSED_WEATHER_CSV))
    return pd.DataFrame()


def _load_merged_data() -> pd.DataFrame:
    """加载合并后的数据"""
    if MERGED_DATA_CSV.exists():
        return pd.read_csv(str(MERGED_DATA_CSV))
    return pd.DataFrame()


@app.route("/api/overview", methods=["GET"])
def get_overview():
    """返回数据集基本统计信息和数据量

    Returns:
        JSON: {
            total_records: 总记录数,
            product_count: 农产品种类数,
            region_count: 地区数,
            date_range: {start, end},
            weather_record_count: 气象数据记录数,
            products: 农产品列表,
            regions: 地区列表
        }
    """
    price_df = _load_price_data()
    weather_df = _load_weather_data()

    if price_df.empty:
        return jsonify({
            "total_records": 0,
            "product_count": 0,
            "region_count": 0,
            "date_range": {"start": None, "end": None},
            "weather_record_count": 0,
            "products": [],
            "regions": [],
            "data_quality": {
                "missing_ratio": 0,
                "completeness": 1.0,
            },
        })

    products = sorted(price_df["product_name"].unique().tolist())
    regions = sorted(price_df["region"].unique().tolist())
    dates = pd.to_datetime(price_df["date"])

    # 数据质量信息
    total_cells = price_df.size
    missing_cells = int(price_df.isnull().sum().sum())
    missing_ratio = round(missing_cells / total_cells, 4) if total_cells > 0 else 0
    completeness = round(1 - missing_ratio, 4)

    return jsonify({
        "total_records": len(price_df),
        "product_count": len(products),
        "region_count": len(regions),
        "date_range": {
            "start": dates.min().strftime("%Y-%m-%d"),
            "end": dates.max().strftime("%Y-%m-%d"),
        },
        "weather_record_count": len(weather_df),
        "products": products,
        "regions": regions,
        "data_quality": {
            "missing_ratio": missing_ratio,
            "completeness": completeness,
        },
    })


@app.route("/api/price-trends", methods=["GET"])
def get_price_trends():
    """返回价格趋势数据，支持按product和region参数筛选

    Query params:
        product (optional): 农产品名称筛选
        region (optional): 地区筛选

    Returns:
        JSON: {
            data: [{date, product_name, average_price}, ...],
            filters: {products: [...], regions: [...]}
        }
    """
    price_df = _load_price_data()

    if price_df.empty:
        return jsonify({"data": [], "filters": {"products": [], "regions": []}})

    # 获取可用的筛选选项
    all_products = sorted(price_df["product_name"].unique().tolist())
    all_regions = sorted(price_df["region"].unique().tolist())

    # 应用筛选条件
    product_filter = request.args.get("product")
    region_filter = request.args.get("region")

    filtered_df = price_df.copy()
    if product_filter:
        filtered_df = filtered_df[filtered_df["product_name"] == product_filter]
    if region_filter:
        filtered_df = filtered_df[filtered_df["region"] == region_filter]

    # 按日期和产品分组计算均价
    if filtered_df.empty:
        trend_data = []
    else:
        trend_grouped = (
            filtered_df.groupby(["date", "product_name"])["average_price"]
            .mean()
            .reset_index()
        )
        trend_grouped = trend_grouped.sort_values("date")
        trend_data = trend_grouped.to_dict(orient="records")

    return jsonify({
        "data": trend_data,
        "filters": {
            "products": all_products,
            "regions": all_regions,
        },
    })


@app.route("/api/weather-impact", methods=["GET"])
def get_weather_impact():
    """返回气象因素与农产品价格的相关性数据（按品类分组分析）

    Returns:
        JSON: {
            weather_cols: [...],          # 气象因素英文名列表
            weather_labels: {...},        # 气象因素中文名映射
            products: [...],              # 品类列表
            by_product: {                 # 每个品类的相关系数
                product_name: { weather_col: corr_value, ... }
            },
            scatter_by_product: {         # 每个品类的散点数据 [temp, price]
                product_name: [[x, y], ...]
            }
        }
    """
    merged_df = _load_merged_data()

    if merged_df.empty:
        return jsonify({
            "correlation_matrix": {},
            "columns": [],
            "column_labels": {},
            "weather_cols": [],
            "weather_labels": {},
            "products": [],
            "by_product": {},
            "scatter_by_product": {},
        })

    weather_cols = [
        "average_temperature",
        "rainfall",
        "humidity",
        "sunshine_duration",
    ]
    weather_labels = {
        "average_temperature": "平均气温",
        "rainfall": "降雨量",
        "humidity": "湿度",
        "sunshine_duration": "日照时长",
    }

    available_weather = [c for c in weather_cols if c in merged_df.columns]
    products = sorted(merged_df["product_name"].unique().tolist()) if "product_name" in merged_df.columns else []

    matrix_cols = ["average_price"] + available_weather
    matrix_df = merged_df[matrix_cols].apply(pd.to_numeric, errors="coerce").dropna(how="all")
    if len(matrix_df.columns) >= 2 and not matrix_df.empty:
        corr_matrix_df = matrix_df.corr()
        correlation_matrix = {
            col: {
                row: round(float(value), 4) if not pd.isna(value) else None
                for row, value in corr_matrix_df[col].items()
            }
            for col in corr_matrix_df.columns
        }
        matrix_columns = corr_matrix_df.columns.tolist()
    else:
        correlation_matrix = {}
        matrix_columns = []

    column_labels = {
        "average_price": "平均价格",
        **weather_labels,
    }

    by_product = {}
    scatter_by_product = {}

    for product in products:
        sub = merged_df[merged_df["product_name"] == product].copy()
        cols = available_weather + ["average_price"]
        sub_clean = sub[cols].dropna()

        # 各气象因素与均价的相关系数
        corr = sub_clean.corr()["average_price"]
        by_product[product] = {
            col: round(float(corr[col]), 4) if col in corr.index and not pd.isna(corr[col]) else None
            for col in available_weather
        }

        # 散点数据：气温 vs 价格（每个品类最多300点）
        if "average_temperature" in sub_clean.columns:
            scatter_sub = sub_clean[["average_temperature", "average_price"]].head(300)
            scatter_by_product[product] = [
                [round(float(r[0]), 2), round(float(r[1]), 3)]
                for r in scatter_sub.itertuples(index=False)
            ]

    return jsonify({
        "correlation_matrix": correlation_matrix,
        "columns": matrix_columns,
        "column_labels": column_labels,
        "weather_cols": available_weather,
        "weather_labels": weather_labels,
        "products": products,
        "by_product": by_product,
        "scatter_by_product": scatter_by_product,
    })


@app.route("/api/predictions", methods=["GET"])
def get_predictions():
    """返回预测结果对比数据和模型误差指标"""
    merged_df = _load_merged_data()

    if merged_df.empty:
        return jsonify({"metrics": None, "predictions": [], "model_available": False})

    try:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        from sklearn.model_selection import train_test_split

        df = merged_df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        df["day_of_week"] = df["date"].dt.dayofweek
        df["day_of_year"] = df["date"].dt.dayofyear
        df["season"] = df["month"].apply(
            lambda m: 1 if m in (3, 4, 5) else (2 if m in (6, 7, 8) else (3 if m in (9, 10, 11) else 4))
        )

        # 品类编码（关键特征，缺少它会导致 R² 为负）
        if "product_name" in df.columns:
            products = sorted(df["product_name"].unique())
            product_map = {p: i for i, p in enumerate(products)}
            df["product_encoded"] = df["product_name"].map(product_map)

        # 地区编码
        if "region" in df.columns:
            region_map = {r: i for i, r in enumerate(sorted(df["region"].unique()))}
            df["region_encoded"] = df["region"].map(region_map)

        feature_cols = ["year", "month", "day_of_week", "day_of_year", "season"]
        if "region_encoded" in df.columns:
            feature_cols.append("region_encoded")
        if "product_encoded" in df.columns:
            feature_cols.append("product_encoded")
        for col in ["average_temperature", "highest_temperature", "lowest_temperature",
                    "rainfall", "humidity", "sunshine_duration"]:
            if col in df.columns:
                feature_cols.append(col)

        X = df[feature_cols].fillna(0)
        y = df["average_price"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # 尝试加载已保存模型，否则即时训练
        model = None
        if RANDOM_FOREST_MODEL.exists():
            try:
                import joblib
                saved = joblib.load(str(RANDOM_FOREST_MODEL))
                saved_features = list(getattr(saved, "feature_names_in_", []))
                if saved_features and saved_features == feature_cols:
                    model = saved
                elif not saved_features and hasattr(saved, "n_features_in_") and saved.n_features_in_ == len(feature_cols):
                    model = saved
            except Exception:
                pass

        if model is None:
            model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
            model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        mae = float(mean_absolute_error(y_test, y_pred))
        mse = float(mean_squared_error(y_test, y_pred))
        rmse = float(np.sqrt(mse))
        r_squared = float(r2_score(y_test, y_pred))

        # 前100个样本的对比数据
        predictions = [
            {"actual": round(float(a), 4), "predicted": round(float(p), 4)}
            for a, p in zip(y_test.values[:100], y_pred[:100])
        ]

        return jsonify({
            "metrics": {
                "mae": round(mae, 4),
                "mse": round(mse, 4),
                "rmse": round(rmse, 4),
                "r_squared": round(r_squared, 4),
            },
            "predictions": predictions,
            "model_available": True,
        })

    except Exception as e:
        return jsonify({"metrics": None, "predictions": [], "model_available": False, "error": str(e)})


if __name__ == "__main__":
    app.run(
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        debug=API_CONFIG["debug"],
    )
