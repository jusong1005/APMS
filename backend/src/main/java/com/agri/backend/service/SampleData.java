package com.agri.backend.service;

import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

final class SampleData {
    private SampleData() {
    }

    static Map<String, Object> map(Object... pairs) {
        Map<String, Object> result = new LinkedHashMap<>();
        for (int index = 0; index < pairs.length; index += 2) {
            result.put(String.valueOf(pairs[index]), pairs[index + 1]);
        }
        return result;
    }

    static Map<String, Object> dashboardOverview() {
        return map(
            "collectionRecords", 126840,
            "marketCount", 1528,
            "productCount", 512,
            "alertCount", 24,
            "updatedAt", LocalDateTime.now().toString(),
            "cards", List.of(
                map("label", "今日采集记录", "value", 126840, "change", "+12.4%", "trend", "up"),
                map("label", "覆盖市场主体", "value", 1528, "change", "+36", "trend", "up"),
                map("label", "重点农产品", "value", 512, "change", "+18", "trend", "up"),
                map("label", "异常波动预警", "value", 24, "change", "-8.1%", "trend", "down")
            )
        );
    }

    static List<Map<String, Object>> dashboardTrend() {
        return List.of(
            map("date", "2026-05-19", "average_price", 4.21, "record_count", 1280),
            map("date", "2026-05-20", "average_price", 4.33, "record_count", 1324),
            map("date", "2026-05-21", "average_price", 4.27, "record_count", 1296),
            map("date", "2026-05-22", "average_price", 4.42, "record_count", 1411),
            map("date", "2026-05-23", "average_price", 4.48, "record_count", 1388),
            map("date", "2026-05-24", "average_price", 4.39, "record_count", 1360),
            map("date", "2026-05-25", "average_price", 4.56, "record_count", 1442)
        );
    }

    static List<Map<String, Object>> latestAlerts() {
        return List.of(
            map("id", "alert-001", "product_name", "番茄", "region", "山东", "change_rate", 18.6, "level", "medium", "status", "open", "detected_at", LocalDateTime.now().minusMinutes(16).toString()),
            map("id", "alert-002", "product_name", "玉米", "region", "四川", "change_rate", 4.1, "level", "low", "status", "open", "detected_at", LocalDateTime.now().minusMinutes(31).toString()),
            map("id", "alert-003", "product_name", "苹果", "region", "河南", "change_rate", -12.2, "level", "high", "status", "acknowledged", "detected_at", LocalDateTime.now().minusHours(1).toString())
        );
    }

    static List<Map<String, Object>> tasks() {
        return List.of(
            map("id", "xf-001", "name", "北京新发地价格采集", "source", "新发地批发市场", "frequency", "5分钟/次", "lastSync", "2026-05-30 00:28:12", "successRate", 99.2, "status", "running", "backlog", 128),
            map("id", "sg-002", "name", "寿光蔬菜行情采集", "source", "寿光蔬菜网", "frequency", "10分钟/次", "lastSync", "2026-05-30 00:24:35", "successRate", 97.8, "status", "running", "backlog", 86),
            map("id", "moa-003", "name", "农业农村部价格指数同步", "source", "农业农村部官网", "frequency", "30分钟/次", "lastSync", "2026-05-30 00:02:41", "successRate", 96.4, "status", "running", "backlog", 42),
            map("id", "mofcom-004", "name", "商务部农产品行情采集", "source", "全国农产品商务信息公共服务平台", "frequency", "15分钟/次", "lastSync", "2026-05-29 23:58:09", "successRate", 91.6, "status", "error", "backlog", 624),
            map("id", "weather-005", "name", "气象辅助数据同步", "source", "中国天气网", "frequency", "30分钟/次", "lastSync", "2026-05-30 00:15:53", "successRate", 98.7, "status", "running", "backlog", 73)
        );
    }

    static Map<String, Object> analysisOverview() {
        return map(
            "price_records", 2892,
            "product_count", 5,
            "price_region_count", 31,
            "market_count", 92,
            "average_price_mean", 8.64,
            "average_price_median", 6.28,
            "average_price_stddev", 4.52,
            "price_min_date", "2023-01-01",
            "price_max_date", "2026-05-30"
        );
    }

    static List<Map<String, Object>> productStatistics() {
        return List.of(
            map("product_name", "番茄", "product_category", "蔬菜类", "record_count", 620, "region_count", 31, "mean_price", 4.28, "min_price", 2.1, "max_price", 8.9),
            map("product_name", "玉米", "product_category", "粮食类", "record_count", 584, "region_count", 31, "mean_price", 2.86, "min_price", 1.8, "max_price", 4.6),
            map("product_name", "苹果", "product_category", "水果类", "record_count", 576, "region_count", 31, "mean_price", 7.24, "min_price", 3.7, "max_price", 12.8),
            map("product_name", "大白菜", "product_category", "蔬菜类", "record_count", 548, "region_count", 31, "mean_price", 2.18, "min_price", 0.9, "max_price", 5.1),
            map("product_name", "猪肉", "product_category", "肉禽蛋类", "record_count", 564, "region_count", 31, "mean_price", 21.35, "min_price", 15.4, "max_price", 32.2)
        );
    }

    static List<Map<String, Object>> regionStatistics() {
        return List.of(
            map("region", "北京", "record_count", 228, "product_count", 5, "mean_price", 9.66, "min_price", 1.8, "max_price", 31.4),
            map("region", "山东", "record_count", 246, "product_count", 5, "mean_price", 7.82, "min_price", 1.1, "max_price", 29.2),
            map("region", "四川", "record_count", 214, "product_count", 5, "mean_price", 8.14, "min_price", 1.2, "max_price", 30.6),
            map("region", "河南", "record_count", 205, "product_count", 5, "mean_price", 7.49, "min_price", 1.0, "max_price", 28.8)
        );
    }

    static List<Map<String, Object>> predictions() {
        return List.of(
            map("product", "番茄", "model", "timeSeries", "next7DayAverage", 4.62, "confidence", 0.86, "riskLevel", "medium", "updatedAt", LocalDateTime.now().minusMinutes(12).toString()),
            map("product", "玉米", "model", "weatherAware", "next7DayAverage", 2.91, "confidence", 0.91, "riskLevel", "low", "updatedAt", LocalDateTime.now().minusMinutes(12).toString()),
            map("product", "猪肉", "model", "combined", "next7DayAverage", 22.08, "confidence", 0.82, "riskLevel", "medium", "updatedAt", LocalDateTime.now().minusMinutes(12).toString())
        );
    }

    static Map<String, Object> predictionFactors(String product) {
        return map(
            "product", product,
            "weights", List.of(
                map("factor", "历史价格", "weight", 0.42),
                map("factor", "季节周期", "weight", 0.24),
                map("factor", "气温降雨", "weight", 0.18),
                map("factor", "地区供给", "weight", 0.16)
            )
        );
    }

    static Map<String, Object> settings() {
        return map(
            "apiPrefix", "/api",
            "qualityThreshold", 0.96,
            "alertThresholdPercent", 10,
            "retentionDays", 365,
            "schedulerEnabled", true,
            "updatedAt", LocalDateTime.now().toString()
        );
    }
}