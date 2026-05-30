"""
项目级数据流水线

串联数据清洗、入库验证、统计分析、模型训练和运行摘要输出，
用于把分散模块整合为可重复执行的完整项目流程。
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from backend.data_analyzer import DataAnalyzer
from backend.data_cleaner import DataCleaner
from backend.db_importer import DBImporter
from backend.model_predictor import ModelPredictor
from config import (
    MERGED_DATA_CSV,
    PROCESSED_PRICE_CSV,
    PROCESSED_WEATHER_CSV,
    RANDOM_FOREST_MODEL,
)


def run_pipeline(
    *,
    append: bool = False,
    skip_import: bool = False,
    skip_analysis: bool = False,
    skip_model: bool = False,
) -> Dict[str, Any]:
    """执行完整项目流水线并返回运行摘要。"""
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    cleaner = DataCleaner()
    clean_result = cleaner.run()

    price_df = pd.read_csv(PROCESSED_PRICE_CSV)
    weather_df = pd.read_csv(PROCESSED_WEATHER_CSV)
    merged_df = pd.read_csv(MERGED_DATA_CSV)
    merged_quality = cleaner.validate_quality(merged_df)

    summary: Dict[str, Any] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "data": _build_data_summary(price_df, weather_df, merged_df),
        "quality": {
            "price_quality": clean_result["price_quality"],
            "weather_quality": clean_result["weather_quality"],
            "merged_quality": merged_quality.is_acceptable,
            "price_missing_ratio": clean_result["price_report"].missing_ratio_after,
            "price_duplicate_ratio": clean_result["price_report"].duplicate_ratio_after,
            "weather_missing_ratio": clean_result["weather_report"].missing_ratio_after,
            "weather_duplicate_ratio": clean_result["weather_report"].duplicate_ratio_after,
            "merged_missing_ratio": merged_quality.missing_ratio,
            "merged_duplicate_ratio": merged_quality.duplicate_ratio,
            "issues": merged_quality.issues,
            "cleaning_report": clean_result["report_path"],
        },
        "database": {"skipped": skip_import},
        "analysis": {"skipped": skip_analysis},
        "model": {"skipped": skip_model},
    }

    if not skip_import:
        summary["database"] = _run_database_import(price_df, weather_df, append=append)

    if not skip_analysis:
        summary["analysis"] = _run_analysis(price_df, merged_df)

    if not skip_model:
        summary["model"] = _run_model_training(merged_df)

    summary_path = output_dir / "pipeline_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary["summary_path"] = str(summary_path)
    return summary


def _build_data_summary(
    price_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    merged_df: pd.DataFrame,
) -> Dict[str, Any]:
    dates = pd.to_datetime(price_df["date"]) if not price_df.empty else pd.Series(dtype="datetime64[ns]")
    return {
        "price_records": int(len(price_df)),
        "weather_records": int(len(weather_df)),
        "merged_records": int(len(merged_df)),
        "product_count": int(price_df["product_name"].nunique()) if "product_name" in price_df.columns else 0,
        "region_count": int(price_df["region"].nunique()) if "region" in price_df.columns else 0,
        "products": sorted(price_df["product_name"].dropna().unique().tolist()) if "product_name" in price_df.columns else [],
        "regions": sorted(price_df["region"].dropna().unique().tolist()) if "region" in price_df.columns else [],
        "date_range": {
            "start": dates.min().strftime("%Y-%m-%d") if not dates.empty else None,
            "end": dates.max().strftime("%Y-%m-%d") if not dates.empty else None,
        },
    }


def _run_database_import(
    price_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    *,
    append: bool,
) -> Dict[str, Any]:
    importer = DBImporter.create_with_fallback()
    try:
        if not append:
            importer.clear_table("price_data")
            importer.clear_table("weather_data")

        price_imported = importer.import_price_data(price_df)
        weather_imported = importer.import_weather_data(weather_df)
        return {
            "skipped": False,
            "database_type": "SQLite" if importer.is_sqlite else "MySQL",
            "mode": "append" if append else "replace",
            "price_imported": int(price_imported),
            "weather_imported": int(weather_imported),
            "price_verified": importer.verify_import("price_data", len(price_df)),
            "weather_verified": importer.verify_import("weather_data", len(weather_df)),
        }
    finally:
        importer.close()


def _run_analysis(price_df: pd.DataFrame, merged_df: pd.DataFrame) -> Dict[str, Any]:
    analyzer = DataAnalyzer()
    results = []

    if not price_df.empty:
        results.extend([
            analyzer.analyze_price_trend(price_df),
            analyzer.analyze_monthly_price(price_df),
            analyzer.analyze_regional_difference(price_df),
            analyzer.analyze_price_volatility(price_df),
        ])

    if not merged_df.empty:
        results.append(analyzer.analyze_weather_correlation(merged_df))

    report_path = analyzer.output_dir / "analysis_report.txt"
    report_path.write_text(analyzer.generate_report(results), encoding="utf-8")

    return {
        "skipped": False,
        "charts": [result.chart_path for result in results if result.chart_path],
        "report_path": str(report_path),
    }


def _run_model_training(merged_df: pd.DataFrame) -> Dict[str, Any]:
    predictor = ModelPredictor()
    feature_df = predictor.engineer_features(merged_df)

    if "product_name" in feature_df.columns:
        product_map = {
            product: index
            for index, product in enumerate(sorted(feature_df["product_name"].dropna().unique()))
        }
        feature_df["product_encoded"] = feature_df["product_name"].map(product_map)

    feature_cols: List[str] = [
        "year",
        "month",
        "day_of_week",
        "day_of_year",
        "season",
    ]
    for col in [
        "region_encoded",
        "product_encoded",
        "average_temperature",
        "highest_temperature",
        "lowest_temperature",
        "rainfall",
        "humidity",
        "sunshine_duration",
    ]:
        if col in feature_df.columns:
            feature_cols.append(col)

    X = feature_df[feature_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    y = pd.to_numeric(feature_df["average_price"], errors="coerce")
    valid_mask = y.notna()
    X = X.loc[valid_mask]
    y = y.loc[valid_mask]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=predictor.test_size,
        random_state=predictor.random_state,
    )
    model = predictor.train_random_forest(X_train, y_train)
    metrics = predictor.evaluate_model(model, X_test, y_test)
    predictor.save_model(model, str(RANDOM_FOREST_MODEL))

    return {
        "skipped": False,
        "feature_columns": feature_cols,
        "training_records": int(len(X_train)),
        "test_records": int(len(X_test)),
        "model_path": str(RANDOM_FOREST_MODEL),
        "mae": round(float(metrics.mae), 4),
        "mse": round(float(metrics.mse), 4),
        "rmse": round(float(metrics.rmse), 4),
        "r_squared": round(float(metrics.r_squared), 4) if metrics.r_squared is not None else None,
        "trigger_arima": predictor.should_trigger_arima(metrics),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="运行农产品价格监控平台完整数据流水线")
    parser.add_argument("--append", action="store_true", help="入库时追加数据，默认清空后重导")
    parser.add_argument("--skip-import", action="store_true", help="跳过数据库导入")
    parser.add_argument("--skip-analysis", action="store_true", help="跳过统计分析图表生成")
    parser.add_argument("--skip-model", action="store_true", help="跳过模型训练")
    args = parser.parse_args()

    summary = run_pipeline(
        append=args.append,
        skip_import=args.skip_import,
        skip_analysis=args.skip_analysis,
        skip_model=args.skip_model,
    )

    print("\n[Pipeline] 完整项目流水线执行完成")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())