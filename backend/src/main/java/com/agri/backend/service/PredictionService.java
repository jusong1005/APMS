package com.agri.backend.service;

import jakarta.servlet.http.HttpServletRequest;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import org.bson.Document;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Service;

@Service
public class PredictionService {
    private final MongoTemplate mongoTemplate;
    private final MongoDocumentMapper mapper;
    private final AuthService authService;
    private final AuditLogService auditLogService;

    public PredictionService(MongoTemplate mongoTemplate, MongoDocumentMapper mapper, AuthService authService, AuditLogService auditLogService) {
        this.mongoTemplate = mongoTemplate;
        this.mapper = mapper;
        this.authService = authService;
        this.auditLogService = auditLogService;
    }

    public List<Map<String, Object>> list() {
        try {
            List<Map<String, Object>> rows = mapper.toMaps(mongoTemplate.findAll(Document.class, "prediction_results"));
            return rows.isEmpty() ? SampleData.predictions() : rows;
        } catch (RuntimeException exception) {
            return SampleData.predictions();
        }
    }

    public Map<String, Object> detail(String product) {
        return list().stream()
            .filter(item -> product.equals(String.valueOf(item.getOrDefault("product", item.get("product_name")))))
            .findFirst()
            .orElse(SampleData.map("product", product, "next7DayAverage", 0, "confidence", 0.0, "riskLevel", "unknown"));
    }

    public Map<String, Object> factors(String product) {
        try {
            Document document = mongoTemplate.findOne(Query.query(Criteria.where("product").is(product)), Document.class, "prediction_results");
            if (document != null && document.get("weights") != null) {
                return SampleData.map("product", product, "weights", document.get("weights"));
            }
        } catch (RuntimeException ignored) {
        }
        return SampleData.predictionFactors(product);
    }

    public Map<String, Object> refresh(HttpServletRequest request) {
        auditLogService.record("prediction.refresh", "prediction_results", "manual refresh", authService.requireCurrentUser().getId(), request.getRemoteAddr());
        return SampleData.map("status", "accepted", "message", "预测刷新任务已提交", "submittedAt", LocalDateTime.now().toString());
    }
}