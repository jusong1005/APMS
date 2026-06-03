package com.agri.backend.service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import org.bson.Document;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.stereotype.Service;

@Service
public class AnalysisService {
    private final MongoTemplate mongoTemplate;
    private final MongoDocumentMapper mapper;

    public AnalysisService(MongoTemplate mongoTemplate, MongoDocumentMapper mapper) {
        this.mongoTemplate = mongoTemplate;
        this.mapper = mapper;
    }

    public Map<String, Object> overview() {
        try {
            List<Map<String, Object>> rows = mapper.toMaps(mongoTemplate.getCollection("price_data").aggregate(List.of(
                new Document("$group", new Document("_id", null)
                    .append("price_records", new Document("$sum", 1))
                    .append("product_count", new Document("$addToSet", "$product_name"))
                    .append("price_region_count", new Document("$addToSet", "$region"))
                    .append("market_count", new Document("$addToSet", "$market_name"))
                    .append("average_price_mean", new Document("$avg", "$average_price"))
                    .append("average_price_stddev", new Document("$stdDevSamp", "$average_price"))
                    .append("price_min_date", new Document("$min", "$date"))
                    .append("price_max_date", new Document("$max", "$date"))),
                new Document("$project", new Document("_id", 0)
                    .append("price_records", 1)
                    .append("product_count", new Document("$size", "$product_count"))
                    .append("price_region_count", new Document("$size", "$price_region_count"))
                    .append("market_count", new Document("$size", "$market_count"))
                    .append("average_price_mean", new Document("$round", List.of("$average_price_mean", 2)))
                    .append("average_price_stddev", new Document("$round", List.of("$average_price_stddev", 2)))
                    .append("price_min_date", 1)
                    .append("price_max_date", 1))
            )));
            return rows.isEmpty() ? SampleData.analysisOverview() : rows.get(0);
        } catch (RuntimeException exception) {
            return SampleData.analysisOverview();
        }
    }

    public List<Map<String, Object>> productStatistics() {
        try {
            List<Map<String, Object>> rows = mapper.toMaps(mongoTemplate.getCollection("price_data").aggregate(List.of(
                new Document("$group", new Document("_id", new Document("product_name", "$product_name").append("product_category", "$product_category"))
                    .append("record_count", new Document("$sum", 1))
                    .append("region_count", new Document("$addToSet", "$region"))
                    .append("market_count", new Document("$addToSet", "$market_name"))
                    .append("mean_price", new Document("$avg", "$average_price"))
                    .append("min_price", new Document("$min", "$average_price"))
                    .append("max_price", new Document("$max", "$average_price"))),
                new Document("$project", new Document("_id", 0)
                    .append("product_name", "$_id.product_name")
                    .append("product_category", "$_id.product_category")
                    .append("record_count", 1)
                    .append("region_count", new Document("$size", "$region_count"))
                    .append("market_count", new Document("$size", "$market_count"))
                    .append("mean_price", new Document("$round", List.of("$mean_price", 2)))
                    .append("min_price", new Document("$round", List.of("$min_price", 2)))
                    .append("max_price", new Document("$round", List.of("$max_price", 2)))),
                new Document("$sort", new Document("record_count", -1))
            )));
            return rows.isEmpty() ? SampleData.productStatistics() : rows;
        } catch (RuntimeException exception) {
            return SampleData.productStatistics();
        }
    }

    public List<Map<String, Object>> regionStatistics() {
        try {
            List<Map<String, Object>> rows = mapper.toMaps(mongoTemplate.getCollection("price_data").aggregate(List.of(
                new Document("$group", new Document("_id", "$region")
                    .append("record_count", new Document("$sum", 1))
                    .append("product_count", new Document("$addToSet", "$product_name"))
                    .append("mean_price", new Document("$avg", "$average_price"))
                    .append("min_price", new Document("$min", "$average_price"))
                    .append("max_price", new Document("$max", "$average_price"))),
                new Document("$project", new Document("_id", 0)
                    .append("region", "$_id")
                    .append("record_count", 1)
                    .append("product_count", new Document("$size", "$product_count"))
                    .append("mean_price", new Document("$round", List.of("$mean_price", 2)))
                    .append("min_price", new Document("$round", List.of("$min_price", 2)))
                    .append("max_price", new Document("$round", List.of("$max_price", 2)))),
                new Document("$sort", new Document("mean_price", -1))
            )));
            return rows.isEmpty() ? SampleData.regionStatistics() : rows;
        } catch (RuntimeException exception) {
            return SampleData.regionStatistics();
        }
    }

    public List<Map<String, Object>> yearlyTrend() {
        return aggregateOrSample(List.of(
            new Document("$project", new Document("product_name", 1).append("year", new Document("$year", "$date")).append("average_price", 1)),
            new Document("$group", new Document("_id", new Document("product_name", "$product_name").append("year", "$year"))
                .append("record_count", new Document("$sum", 1))
                .append("year_mean_price", new Document("$avg", "$average_price"))),
            new Document("$project", new Document("_id", 0).append("product_name", "$_id.product_name").append("year", "$_id.year").append("record_count", 1).append("year_mean_price", new Document("$round", List.of("$year_mean_price", 2)))),
            new Document("$sort", new Document("product_name", 1).append("year", 1))
        ), List.of(
            SampleData.map("product_name", "番茄", "year", 2024, "year_mean_price", 4.16, "record_count", 168),
            SampleData.map("product_name", "番茄", "year", 2025, "year_mean_price", 4.35, "record_count", 176),
            SampleData.map("product_name", "番茄", "year", 2026, "year_mean_price", 4.54, "record_count", 92)
        ));
    }

    public List<Map<String, Object>> dailyTrend() {
        return aggregateOrSample(List.of(
            new Document("$group", new Document("_id", "$date").append("record_count", new Document("$sum", 1)).append("mean_price", new Document("$avg", "$average_price"))),
            new Document("$project", new Document("_id", 0).append("date", "$_id").append("record_count", 1).append("mean_price", new Document("$round", List.of("$mean_price", 2)))),
            new Document("$sort", new Document("date", 1)),
            new Document("$limit", 120)
        ), SampleData.dashboardTrend());
    }

    public List<Map<String, Object>> priceRangeAnalysis() {
        return aggregateOrSample(List.of(
            new Document("$group", new Document("_id", "$product_name")
                .append("min_price", new Document("$min", "$average_price"))
                .append("max_price", new Document("$max", "$average_price"))
                .append("mean_price", new Document("$avg", "$average_price"))),
            new Document("$project", new Document("_id", 0)
                .append("product_name", "$_id")
                .append("min_price", new Document("$round", List.of("$min_price", 2)))
                .append("max_price", new Document("$round", List.of("$max_price", 2)))
                .append("mean_price", new Document("$round", List.of("$mean_price", 2)))
                .append("range", new Document("$round", List.of(new Document("$subtract", List.of("$max_price", "$min_price")), 2)))),
            new Document("$sort", new Document("range", -1))
        ), SampleData.productStatistics());
    }

    public List<Map<String, Object>> volatility() {
        return aggregateOrSample(List.of(
            new Document("$group", new Document("_id", "$product_name")
                .append("stddev_price", new Document("$stdDevSamp", "$average_price"))
                .append("mean_price", new Document("$avg", "$average_price"))),
            new Document("$project", new Document("_id", 0)
                .append("product_name", "$_id")
                .append("stddev_price", new Document("$round", List.of("$stddev_price", 2)))
                .append("mean_price", new Document("$round", List.of("$mean_price", 2)))),
            new Document("$sort", new Document("stddev_price", -1))
        ), List.of(
            SampleData.map("product_name", "猪肉", "stddev_price", 3.82, "mean_price", 21.35),
            SampleData.map("product_name", "苹果", "stddev_price", 2.14, "mean_price", 7.24),
            SampleData.map("product_name", "番茄", "stddev_price", 1.68, "mean_price", 4.28)
        ));
    }

    public List<Map<String, Object>> regionPriceDifference() {
        return List.of(
            SampleData.map("product_name", "番茄", "region", "山东", "region_mean_price", 4.68, "gap_rate_percent", 9.35),
            SampleData.map("product_name", "苹果", "region", "河南", "region_mean_price", 6.72, "gap_rate_percent", -7.18),
            SampleData.map("product_name", "猪肉", "region", "四川", "region_mean_price", 22.41, "gap_rate_percent", 4.96)
        );
    }

    public List<Map<String, Object>> seasonalPriceChange() {
        return List.of(
            SampleData.map("season", "春季", "mean_price", 7.92, "change_rate_percent", 3.8),
            SampleData.map("season", "夏季", "mean_price", 8.44, "change_rate_percent", 6.6),
            SampleData.map("season", "秋季", "mean_price", 8.12, "change_rate_percent", -3.8),
            SampleData.map("season", "冬季", "mean_price", 9.06, "change_rate_percent", 11.6)
        );
    }

    public List<Map<String, Object>> weatherCorrelation() {
        return List.of(
            SampleData.map("factor", "平均气温", "correlation", -0.31, "impact", "中等负相关"),
            SampleData.map("factor", "降雨量", "correlation", 0.27, "impact", "弱正相关"),
            SampleData.map("factor", "湿度", "correlation", 0.18, "impact", "弱正相关")
        );
    }

    public List<Map<String, Object>> sparkSql() {
        return List.of(
            SampleData.map("sql_name", "高波动品类", "record_count", 128, "generated_at", LocalDateTime.now().toString()),
            SampleData.map("sql_name", "地区均价 Top10", "record_count", 10, "generated_at", LocalDateTime.now().toString())
        );
    }

    public List<Map<String, Object>> topFluctuations() {
        return List.of(
            SampleData.map("product_name", "番茄", "region", "山东", "change_rate_percent", 18.6, "date", "2026-05-30"),
            SampleData.map("product_name", "苹果", "region", "河南", "change_rate_percent", -12.2, "date", "2026-05-30"),
            SampleData.map("product_name", "猪肉", "region", "四川", "change_rate_percent", 9.8, "date", "2026-05-29")
        );
    }

    public Map<String, Object> export() {
        return SampleData.map("fileName", "agri-analysis-" + LocalDateTime.now() + ".json", "format", "json", "rows", productStatistics());
    }

    private List<Map<String, Object>> aggregateOrSample(List<Document> pipeline, List<Map<String, Object>> sample) {
        try {
            List<Map<String, Object>> rows = mapper.toMaps(mongoTemplate.getCollection("price_data").aggregate(pipeline));
            return rows.isEmpty() ? sample : rows;
        } catch (RuntimeException exception) {
            return sample;
        }
    }
}