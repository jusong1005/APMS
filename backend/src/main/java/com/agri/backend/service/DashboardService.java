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
                    SampleData.map("label", "今日采集记录", "value", collectionRecords, "change", "+实时", "trend", "up"),
                    SampleData.map("label", "覆盖市场主体", "value", marketCount, "change", "+MongoDB", "trend", "up"),
                    SampleData.map("label", "重点农产品", "value", productCount, "change", "+MongoDB", "trend", "up"),
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

    private Map<Object, Object> readRedisHash(String suffix) {
        try {
            return redisTemplate.opsForHash().entries(redisPrefix + ":" + suffix);
        } catch (RuntimeException exception) {
            return Map.of();
        }
    }
}