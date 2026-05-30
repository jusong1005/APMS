"""
API接口集成测试

测试Flask后端REST API各接口的正确性：
- /api/overview: 数据集基本统计信息
- /api/price-trends: 价格趋势数据（支持筛选）
- /api/weather-impact: 气象因素与价格相关性
- /api/predictions: 预测结果和模型指标

验证需求：6.1, 6.4
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from backend.app import app


@pytest.fixture
def client():
    """创建Flask测试客户端"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def empty_client():
    """创建Flask测试客户端，模拟无数据文件的情况"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_cors_allows_local_frontend_origins(client):
    """CORS应允许常用本地前端开发地址访问API"""
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    for origin in allowed_origins:
        response = client.get("/api/overview", headers={"Origin": origin})
        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") == origin


# ============================================================
# /api/overview 接口测试
# ============================================================


class TestOverviewEndpoint:
    """测试 /api/overview 接口"""

    def test_returns_json(self, client):
        """接口应返回JSON格式响应"""
        response = client.get("/api/overview")
        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_response_has_expected_keys(self, client):
        """响应应包含所有预期的键"""
        response = client.get("/api/overview")
        data = response.get_json()
        expected_keys = {
            "total_records",
            "product_count",
            "region_count",
            "date_range",
            "weather_record_count",
            "products",
            "regions",
        }
        assert expected_keys.issubset(set(data.keys()))

    def test_response_data_types(self, client):
        """响应字段应具有正确的数据类型"""
        response = client.get("/api/overview")
        data = response.get_json()

        assert isinstance(data["total_records"], int)
        assert isinstance(data["product_count"], int)
        assert isinstance(data["region_count"], int)
        assert isinstance(data["date_range"], dict)
        assert isinstance(data["weather_record_count"], int)
        assert isinstance(data["products"], list)
        assert isinstance(data["regions"], list)

    def test_date_range_structure(self, client):
        """date_range应包含start和end键"""
        response = client.get("/api/overview")
        data = response.get_json()
        date_range = data["date_range"]
        assert "start" in date_range
        assert "end" in date_range


# ============================================================
# /api/price-trends 接口测试
# ============================================================


class TestPriceTrendsEndpoint:
    """测试 /api/price-trends 接口"""

    def test_returns_json(self, client):
        """接口应返回JSON格式响应"""
        response = client.get("/api/price-trends")
        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_response_has_expected_keys(self, client):
        """响应应包含data和filters键"""
        response = client.get("/api/price-trends")
        data = response.get_json()
        assert "data" in data
        assert "filters" in data

    def test_filters_structure(self, client):
        """filters应包含products和regions列表"""
        response = client.get("/api/price-trends")
        data = response.get_json()
        filters = data["filters"]
        assert "products" in filters
        assert "regions" in filters
        assert isinstance(filters["products"], list)
        assert isinstance(filters["regions"], list)

    def test_no_filter_returns_all_data(self, client):
        """无筛选参数时应返回所有数据"""
        response = client.get("/api/price-trends")
        data = response.get_json()
        # 无筛选时data列表不应为空（假设有处理后的数据）
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

    def test_product_filter(self, client):
        """按product筛选应只返回匹配的产品数据"""
        # 先获取可用产品列表
        overview_resp = client.get("/api/overview")
        products = overview_resp.get_json()["products"]
        if not products:
            pytest.skip("无可用产品数据")

        target_product = products[0]
        response = client.get(f"/api/price-trends?product={target_product}")
        data = response.get_json()

        assert isinstance(data["data"], list)
        # 所有返回的数据应只包含目标产品
        for record in data["data"]:
            assert record["product_name"] == target_product

    def test_region_filter(self, client):
        """按region筛选应只返回匹配的地区数据"""
        # 先获取可用地区列表
        overview_resp = client.get("/api/overview")
        regions = overview_resp.get_json()["regions"]
        if not regions:
            pytest.skip("无可用地区数据")

        target_region = regions[0]
        response = client.get(f"/api/price-trends?region={target_region}")
        data = response.get_json()

        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

    def test_invalid_filter_returns_empty_data(self, client):
        """无效筛选参数应返回空数据列表"""
        response = client.get("/api/price-trends?product=不存在的产品XYZ")
        data = response.get_json()

        assert isinstance(data["data"], list)
        assert len(data["data"]) == 0


# ============================================================
# /api/weather-impact 接口测试
# ============================================================


class TestWeatherImpactEndpoint:
    """测试 /api/weather-impact 接口"""

    def test_returns_json(self, client):
        """接口应返回JSON格式响应"""
        response = client.get("/api/weather-impact")
        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_response_has_expected_keys(self, client):
        """响应应包含correlation_matrix、columns和column_labels键"""
        response = client.get("/api/weather-impact")
        data = response.get_json()
        assert "correlation_matrix" in data
        assert "columns" in data
        assert "column_labels" in data

    def test_correlation_values_in_range(self, client):
        """相关系数值应在-1到1之间"""
        response = client.get("/api/weather-impact")
        data = response.get_json()
        corr_matrix = data["correlation_matrix"]

        if not corr_matrix:
            pytest.skip("无相关性数据")

        for col, row_values in corr_matrix.items():
            for row, value in row_values.items():
                if value is not None:  # None表示NaN
                    assert -1.0 <= value <= 1.0, (
                        f"相关系数 {col}-{row} = {value} 超出[-1, 1]范围"
                    )

    def test_columns_match_matrix(self, client):
        """columns列表应与correlation_matrix的键一致"""
        response = client.get("/api/weather-impact")
        data = response.get_json()

        if not data["columns"]:
            pytest.skip("无列数据")

        assert set(data["columns"]) == set(data["correlation_matrix"].keys())


# ============================================================
# /api/predictions 接口测试
# ============================================================


class TestPredictionsEndpoint:
    """测试 /api/predictions 接口"""

    def test_returns_json(self, client):
        """接口应返回JSON格式响应"""
        response = client.get("/api/predictions")
        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_response_has_expected_keys(self, client):
        """响应应包含metrics、predictions和model_available键"""
        response = client.get("/api/predictions")
        data = response.get_json()
        assert "metrics" in data
        assert "predictions" in data
        assert "model_available" in data

    def test_model_available_is_boolean(self, client):
        """model_available应为布尔值"""
        response = client.get("/api/predictions")
        data = response.get_json()
        assert isinstance(data["model_available"], bool)

    def test_metrics_structure_when_present(self, client):
        """当metrics存在时应包含mae、mse、rmse、r_squared"""
        response = client.get("/api/predictions")
        data = response.get_json()

        if data["metrics"] is None:
            pytest.skip("模型指标不可用")

        metrics = data["metrics"]
        assert "mae" in metrics
        assert "mse" in metrics
        assert "rmse" in metrics
        assert "r_squared" in metrics

        # 指标值应为数值类型
        assert isinstance(metrics["mae"], (int, float))
        assert isinstance(metrics["mse"], (int, float))
        assert isinstance(metrics["rmse"], (int, float))
        assert isinstance(metrics["r_squared"], (int, float))

    def test_predictions_is_list(self, client):
        """predictions应为列表"""
        response = client.get("/api/predictions")
        data = response.get_json()
        assert isinstance(data["predictions"], list)

    def test_prediction_record_structure(self, client):
        """预测记录应包含actual和predicted字段"""
        response = client.get("/api/predictions")
        data = response.get_json()

        if not data["predictions"]:
            pytest.skip("无预测数据")

        record = data["predictions"][0]
        assert "actual" in record
        assert "predicted" in record
        assert isinstance(record["actual"], (int, float))
        assert isinstance(record["predicted"], (int, float))



# ============================================================
# 无数据时的空结果处理测试
# ============================================================


class TestEmptyDataResponses:
    """测试当数据文件不存在时，各接口返回正确的默认空响应"""

    def test_overview_empty_when_no_data(self, client):
        """无数据文件时 /api/overview 应返回零值默认响应"""
        with patch("backend.app._load_price_data", return_value=pd.DataFrame()):
            with patch("backend.app._load_weather_data", return_value=pd.DataFrame()):
                response = client.get("/api/overview")
                assert response.status_code == 200
                data = response.get_json()

                assert data["total_records"] == 0
                assert data["product_count"] == 0
                assert data["region_count"] == 0
                assert data["date_range"]["start"] is None
                assert data["date_range"]["end"] is None
                assert data["weather_record_count"] == 0
                assert data["products"] == []
                assert data["regions"] == []

    def test_price_trends_empty_when_no_data(self, client):
        """无数据文件时 /api/price-trends 应返回空数据列表"""
        with patch("backend.app._load_price_data", return_value=pd.DataFrame()):
            response = client.get("/api/price-trends")
            assert response.status_code == 200
            data = response.get_json()

            assert data["data"] == []
            assert data["filters"]["products"] == []
            assert data["filters"]["regions"] == []

    def test_weather_impact_empty_when_no_data(self, client):
        """无数据文件时 /api/weather-impact 应返回空相关性矩阵"""
        with patch("backend.app._load_merged_data", return_value=pd.DataFrame()):
            response = client.get("/api/weather-impact")
            assert response.status_code == 200
            data = response.get_json()

            assert data["correlation_matrix"] == {}
            assert data["columns"] == []
            assert data["column_labels"] == {}

    def test_predictions_empty_when_no_data(self, client):
        """无数据文件时 /api/predictions 应返回空预测结果"""
        with patch("backend.app._load_merged_data", return_value=pd.DataFrame()):
            response = client.get("/api/predictions")
            assert response.status_code == 200
            data = response.get_json()

            assert data["metrics"] is None
            assert data["predictions"] == []
            assert data["model_available"] is False

    def test_price_trends_with_filter_on_empty_data(self, client):
        """无数据时带筛选参数的请求也应返回有效JSON"""
        with patch("backend.app._load_price_data", return_value=pd.DataFrame()):
            response = client.get("/api/price-trends?product=番茄&region=北京")
            assert response.status_code == 200
            data = response.get_json()

            assert data["data"] == []
            assert isinstance(data["filters"], dict)

    def test_all_endpoints_return_valid_json_on_empty(self, client):
        """所有接口在无数据时都应返回有效的JSON响应（不报500错误）"""
        with patch("backend.app._load_price_data", return_value=pd.DataFrame()):
            with patch("backend.app._load_weather_data", return_value=pd.DataFrame()):
                with patch("backend.app._load_merged_data", return_value=pd.DataFrame()):
                    endpoints = [
                        "/api/overview",
                        "/api/price-trends",
                        "/api/weather-impact",
                        "/api/predictions",
                    ]
                    for endpoint in endpoints:
                        response = client.get(endpoint)
                        assert response.status_code == 200, (
                            f"{endpoint} 返回状态码 {response.status_code}，期望 200"
                        )
                        assert response.content_type == "application/json", (
                            f"{endpoint} 返回类型 {response.content_type}，期望 application/json"
                        )
                        # 确保能正确解析JSON
                        data = response.get_json()
                        assert data is not None, f"{endpoint} 返回的JSON为None"
