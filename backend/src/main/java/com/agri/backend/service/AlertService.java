package com.agri.backend.service;

import com.agri.backend.exception.BusinessException;
import jakarta.servlet.http.HttpServletRequest;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.bson.Document;
import org.springframework.data.domain.Sort;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
public class AlertService {
    private final MongoTemplate mongoTemplate;
    private final MongoDocumentMapper mapper;
    private final AuthService authService;
    private final AuditLogService auditLogService;

    public AlertService(MongoTemplate mongoTemplate, MongoDocumentMapper mapper, AuthService authService, AuditLogService auditLogService) {
        this.mongoTemplate = mongoTemplate;
        this.mapper = mapper;
        this.authService = authService;
        this.auditLogService = auditLogService;
    }

    public List<Map<String, Object>> rules() {
        List<Map<String, Object>> rows = mapper.toMaps(mongoTemplate.find(new Query().with(Sort.by("product_name")), Document.class, "alert_rules"));
        return rows.isEmpty() ? List.of(
            SampleData.map("id", "rule-001", "product_name", "番茄", "region", "山东", "threshold_percent", 10, "enabled", true),
            SampleData.map("id", "rule-002", "product_name", "猪肉", "region", "全国", "threshold_percent", 8, "enabled", true)
        ) : rows;
    }

    public Map<String, Object> createRule(Map<String, Object> body, HttpServletRequest request) {
        String id = String.valueOf(body.getOrDefault("id", "rule-" + UUID.randomUUID()));
        Document document = new Document(body).append("_id", id).append("created_at", LocalDateTime.now()).append("updated_at", LocalDateTime.now());
        mongoTemplate.save(document, "alert_rules");
        audit("alert.rule.create", id, request);
        return mapper.toMap(document);
    }

    public Map<String, Object> updateRule(String id, Map<String, Object> body, HttpServletRequest request) {
        Document document = find("alert_rules", id, "预警规则不存在");
        body.forEach((key, value) -> {
            if (!"id".equals(key) && !"_id".equals(key)) {
                document.put(key, value);
            }
        });
        document.put("updated_at", LocalDateTime.now());
        mongoTemplate.save(document, "alert_rules");
        audit("alert.rule.update", id, request);
        return mapper.toMap(document);
    }

    public void deleteRule(String id, HttpServletRequest request) {
        mongoTemplate.remove(Query.query(Criteria.where("_id").is(id)), "alert_rules");
        audit("alert.rule.delete", id, request);
    }

    public List<Map<String, Object>> records(String status) {
        try {
            Query query = new Query().with(Sort.by(Sort.Direction.DESC, "detected_at"));
            if (StringUtils.hasText(status) && !"all".equalsIgnoreCase(status)) {
                query.addCriteria(Criteria.where("status").is(status));
            }
            List<Map<String, Object>> rows = mapper.toMaps(mongoTemplate.find(query, Document.class, "alert_records"));
            return rows.isEmpty() ? SampleData.latestAlerts() : rows;
        } catch (RuntimeException exception) {
            return SampleData.latestAlerts();
        }
    }

    public Map<String, Object> ack(String id, HttpServletRequest request) {
        return updateRecordStatus(id, "acknowledged", request);
    }

    public Map<String, Object> close(String id, HttpServletRequest request) {
        return updateRecordStatus(id, "closed", request);
    }

    private Map<String, Object> updateRecordStatus(String id, String status, HttpServletRequest request) {
        Document document = find("alert_records", id, "预警记录不存在");
        document.put("status", status);
        document.put(status + "_at", LocalDateTime.now());
        mongoTemplate.save(document, "alert_records");
        audit("alert.record." + status, id, request);
        return mapper.toMap(document);
    }

    private Document find(String collection, String id, String message) {
        Document document = mongoTemplate.findOne(Query.query(Criteria.where("_id").is(id)), Document.class, collection);
        if (document == null) {
            throw new BusinessException(HttpStatus.NOT_FOUND, message);
        }
        return document;
    }

    private void audit(String action, String id, HttpServletRequest request) {
        auditLogService.record(action, "alerts", id, authService.requireCurrentUser().getId(), clientIp(request));
    }

    private String clientIp(HttpServletRequest request) {
        String forwarded = request.getHeader("X-Forwarded-For");
        return StringUtils.hasText(forwarded) ? forwarded.split(",")[0].trim() : request.getRemoteAddr();
    }
}