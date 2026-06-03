package com.agri.backend.service;

import java.time.LocalDateTime;
import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.stereotype.Service;

@Service
public class AuditLogService {
    private static final Logger log = LoggerFactory.getLogger(AuditLogService.class);
    private final MongoTemplate mongoTemplate;

    public AuditLogService(MongoTemplate mongoTemplate) {
        this.mongoTemplate = mongoTemplate;
    }

    public void record(String action, String target, String detail, String userId, String ip) {
        try {
            Document document = new Document()
                .append("action", action)
                .append("target", target)
                .append("detail", detail)
                .append("user_id", userId)
                .append("ip", ip)
                .append("created_at", LocalDateTime.now());
            mongoTemplate.insert(document, "audit_logs");
        } catch (RuntimeException exception) {
            log.warn("Failed to write audit log: {}", exception.getMessage());
        }
    }
}