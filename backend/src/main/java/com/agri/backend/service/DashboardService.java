package com.agri.backend.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.bson.Document;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
public class DashboardService {
    private final MongoTemplate mongoTemplate;
    private final StringRedisTemplate redisTemplate;
    private final MongoDocumentMapper mapper;
    private final ObjectMapper objectMapper;
    private final String redisPrefix;

    public DashboardService(
        MongoTemplate mongoTemplate,
        StringRedisTemplate redisTemplate,
        MongoDocumentMapper mapper,
        ObjectMapper objectMapper,
        @Value("${app.redis.key-prefix}") String redisPrefix
    ) {
        this.mongoTemplate = mongoTemplate;
        this.redisTemplate = redisTemplate;
        this.mapper = mapper;
        this.objectMapper = objectMapper;
        this.redisPrefix = redisPrefix.endsWith(":") ? redisPrefix.substring(0, redisPrefix.length() - 1) : redisPrefix;
    }

    public Map<String, Object> overview() {
        try {
            long collectionRecords = mongoTemplate.getCollection("price_data").countDocuments();
            if (collectionRecords == 0) {
                return SampleData.dashboardOverview();
            }
            long marketCount = distinctCount("price_data", "market_name");
            long productCount = distinctCount("price_data", "product_name");
            long alertCount = alertCount();
            return SampleData.map(
                "collectionRecords", collectionRecords,
                "marketCount", marketCount,
                "productCount", productCount,
                "alertCount", alertCount,
                "cards", List.of(
                    SampleData.map("label", "累计入库记录", "value", collectionRecords, "change", "MongoDB", "trend", "up"),
                    SampleData.map("label", "覆盖市场主体", "value", marketCount, "change", "MongoDB", "trend", "up"),
                    SampleData.map("label", "重点农产品", "value", productCount, "change", "MongoDB", "trend", "up"),
                    SampleData.map("label", "异常波动预警", "value", alertCount, "change", "Redis/Mongo", "trend", alertCount > 0 ? "down" : "up")
                )
            );
        } catch (RuntimeException exception) {
            return SampleData.dashboardOverview();
        }
    }

    public Map<String, Object> realtime() {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("lastBatch", readRedisJson("last_batch"));
        result.put("latestPrices", readRedisJson("latest_prices"));
        result.put("latestAlerts", readRedisJson("latest_alerts"));
        result.put("metrics", readRedisHash("metrics"));
        Object latestPrices = result.get("latestPrices");
        if (!(latestPrices instanceof List<?> priceList && !priceList.isEmpty())) {
            List<Map<String, Object>> mongoLatestPrices = latestMongoPrices();
            if (!mongoLatestPrices.isEmpty()) {
                double latestAverage = mongoLatestPrices.stream()
                    .map(row -> row.get("average_price"))
                    .filter(Number.class::isInstance)
                    .mapToDouble(value -> ((Number) value).doubleValue())
                    .average()
                    .orElse(0);
                result.put("latestPrices", mongoLatestPrices);
                result.put("lastBatch", SampleData.map(
                    "status", "mongo_latest",
                    "batch_count", mongoLatestPrices.size(),
                    "latest_average_price", Math.round(latestAverage * 100.0) / 100.0
                ));
            }
        }
        if (result.values().stream().allMatch(value -> value == null || value instanceof Map<?, ?> map && map.isEmpty())) {
            result.put("lastBatch", SampleData.map("status", "demo", "batch_count", 1280, "realtime_average_price", 4.56));
            result.put("latestPrices", SampleData.productStatistics());
            result.put("latestAlerts", SampleData.latestAlerts());
        }
        return result;
    }

    public List<Map<String, Object>> trend(String product, String region) {
        try {
            List<Document> pipeline = new ArrayList<>();
            Document match = new Document();
            if (StringUtils.hasText(product)) {
                match.append("product_name", product.trim());
            }
            if (StringUtils.hasText(region)) {
                match.append("region", region.trim());
            }
            if (!match.isEmpty()) {
                pipeline.add(new Document("$match", match));
            }
            pipeline.add(new Document("$group", new Document("_id", "$date")
                .append("average_price", new Document("$avg", "$average_price"))
                .append("record_count", new Document("$sum", 1))));
            pipeline.add(new Document("$sort", new Document("_id", 1)));
            pipeline.add(new Document("$limit", 180));
            pipeline.add(new Document("$project", new Document("_id", 0)
                .append("date", "$_id")
                .append("average_price", new Document("$round", List.of("$average_price", 2)))
                .append("record_count", 1)));
            List<Map<String, Object>> rows = mapper.toMaps(mongoTemplate.getCollection("price_data").aggregate(pipeline));
            return rows.isEmpty() ? SampleData.dashboardTrend() : rows;
        } catch (RuntimeException exception) {
            return SampleData.dashboardTrend();
        }
    }

    public List<Map<String, Object>> alerts() {
        Object redisAlerts = readRedisJson("latest_alerts");
        if (redisAlerts instanceof List<?> list && !list.isEmpty()) {
            return list.stream().filter(Map.class::isInstance).map(item -> (Map<String, Object>) item).toList();
        }
        try {
            List<Map<String, Object>> rows = mapper.toMaps(mongoTemplate.getCollection("alert_records").find().sort(new Document("detected_at", -1)).limit(20));
            return rows.isEmpty() ? SampleData.latestAlerts() : rows;
        } catch (RuntimeException exception) {
            return SampleData.latestAlerts();
        }
    }

    private long distinctCount(String collection, String field) {
        return mongoTemplate.getCollection(collection).distinct(field, String.class).into(new ArrayList<>()).size();
    }

    private long alertCount() {
        try {
            Map<Object, Object> metrics = redisTemplate.opsForHash().entries(redisPrefix + ":metrics");
            Object redisAlertCount = metrics.get("alert_count");
            if (redisAlertCount != null) {
                return Long.parseLong(String.valueOf(redisAlertCount));
            }
        } catch (RuntimeException ignored) {
        }
        return mongoTemplate.getCollection("alert_records").countDocuments(new Document("status", new Document("$ne", "closed")));
    }

    private Object readRedisJson(String suffix) {
        try {
            String value = redisTemplate.opsForValue().get(redisPrefix + ":" + suffix);
            if (!StringUtils.hasText(value)) {
                return null;
            }
            return objectMapper.readValue(value, new TypeReference<Object>() {
            });
        } catch (Exception exception) {
            return null;
        }
    }

    private List<Map<String, Object>> latestMongoPrices() {
        try {
            List<Document> pipeline = List.of(
                new Document("$group", new Document("_id", new Document("product_name", "$product_name").append("date", "$date"))
                    .append("product_name", new Document("$first", "$product_name"))
                    .append("product_category", new Document("$first", "$product_category"))
                    .append("market_name", new Document("$first", "$market_name"))
                    .append("region", new Document("$first", "$region"))
                    .append("average_price", new Document("$avg", "$average_price"))
                    .append("record_count", new Document("$sum", 1))
                    .append("regions", new Document("$addToSet", "$region"))),
                new Document("$sort", new Document("product_name", 1).append("_id.date", -1)),
                new Document("$group", new Document("_id", "$product_name")
                    .append("product_name", new Document("$first", "$product_name"))
                    .append("product_category", new Document("$first", "$product_category"))
                    .append("market_name", new Document("$first", "$market_name"))
                    .append("region", new Document("$first", "$region"))
                    .append("latest_date", new Document("$first", "$_id.date"))
                    .append("average_price", new Document("$first", "$average_price"))
                    .append("latest_record_count", new Document("$first", "$record_count"))
                    .append("record_count", new Document("$sum", "$record_count"))
                    .append("region_sets", new Document("$push", "$regions"))
                    .append("prices", new Document("$push", "$average_price"))),
                new Document("$project", new Document("_id", 0)
                    .append("product_name", 1)
                    .append("product_category", 1)
                    .append("market_name", 1)
                    .append("region", 1)
                    .append("date", "$latest_date")
                    .append("average_price", new Document("$round", List.of("$average_price", 2)))
                    .append("price", new Document("$round", List.of("$average_price", 2)))
                    .append("record_count", 1)
                    .append("latest_record_count", 1)
                    .append("region_count", new Document("$size", new Document("$reduce", new Document("input", "$region_sets")
                        .append("initialValue", List.of())
                        .append("in", new Document("$setUnion", List.of("$$value", "$$this"))))))
                    .append("change_rate", new Document("$cond", List.of(
                        new Document("$gt", List.of(new Document("$arrayElemAt", List.of("$prices", 1)), 0)),
                        new Document("$round", List.of(new Document("$multiply", List.of(new Document("$divide", List.of(
                            new Document("$subtract", List.of("$average_price", new Document("$arrayElemAt", List.of("$prices", 1)))),
                            new Document("$arrayElemAt", List.of("$prices", 1))
                        )), 100)), 1)),
                        0
                    )))
                    .append("source", "mongo_latest")),
                new Document("$sort", new Document("date", -1).append("record_count", -1)),
                new Document("$limit", 80)
            );
            return mapper.toMaps(mongoTemplate.getCollection("price_data").aggregate(pipeline));
        } catch (RuntimeException exception) {
            return List.of();
        }
    }

    private Map<Object, Object> readRedisHash(String suffix) {
        try {
            return redisTemplate.opsForHash().entries(redisPrefix + ":" + suffix);
        } catch (RuntimeException exception) {
            return Map.of();
        }
    }
}