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
public class TaskService {
    private final MongoTemplate mongoTemplate;
    private final MongoDocumentMapper mapper;
    private final AuthService authService;
    private final AuditLogService auditLogService;

    public TaskService(MongoTemplate mongoTemplate, MongoDocumentMapper mapper, AuthService authService, AuditLogService auditLogService) {
        this.mongoTemplate = mongoTemplate;
        this.mapper = mapper;
        this.authService = authService;
        this.auditLogService = auditLogService;
    }

    public List<Map<String, Object>> list(String status, String keyword) {
        try {
            Query query = new Query();
            if (StringUtils.hasText(status) && !"all".equalsIgnoreCase(status)) {
                query.addCriteria(Criteria.where("status").is(status));
            }
            if (StringUtils.hasText(keyword)) {
                String pattern = ".*" + keyword.trim() + ".*";
                query.addCriteria(new Criteria().orOperator(Criteria.where("name").regex(pattern, "i"), Criteria.where("source").regex(pattern, "i")));
            }
            query.with(Sort.by(Sort.Direction.ASC, "_id"));
            List<Map<String, Object>> rows = mapper.toMaps(mongoTemplate.find(query, Document.class, "task_records"));
            return rows.isEmpty() ? SampleData.tasks() : rows;
        } catch (RuntimeException exception) {
            return SampleData.tasks();
        }
    }

    public Map<String, Object> create(Map<String, Object> body, HttpServletRequest request) {
        String id = String.valueOf(body.getOrDefault("id", "task-" + UUID.randomUUID()));
        Document document = new Document(body)
            .append("_id", id)
            .append("status", String.valueOf(body.getOrDefault("status", "stopped")))
            .append("created_at", LocalDateTime.now())
            .append("updated_at", LocalDateTime.now());
        mongoTemplate.save(document, "task_records");
        writeLog(id, "create", "创建采集任务");
        auditLogService.record("task.create", "task_records", id, authService.requireCurrentUser().getId(), clientIp(request));
        return mapper.toMap(document);
    }

    public Map<String, Object> update(String id, Map<String, Object> body, HttpServletRequest request) {
        Document document = findDocument(id);
        body.forEach((key, value) -> {
            if (!"id".equals(key) && !"_id".equals(key)) {
                document.put(key, value);
            }
        });
        document.put("updated_at", LocalDateTime.now());
        mongoTemplate.save(document, "task_records");
        writeLog(id, "update", "编辑采集任务");
        auditLogService.record("task.update", "task_records", id, authService.requireCurrentUser().getId(), clientIp(request));
        return mapper.toMap(document);
    }

    public Map<String, Object> start(String id, HttpServletRequest request) {
        return changeStatus(id, "running", "启动任务", request);
    }

    public Map<String, Object> stop(String id, HttpServletRequest request) {
        return changeStatus(id, "stopped", "停止任务", request);
    }

    public List<Map<String, Object>> logs(String id) {
        try {
            Query query = Query.query(Criteria.where("task_id").is(id)).with(Sort.by(Sort.Direction.DESC, "created_at"));
            List<Map<String, Object>> rows = mapper.toMaps(mongoTemplate.find(query, Document.class, "task_logs"));
            return rows.isEmpty() ? List.of(SampleData.map("task_id", id, "level", "INFO", "message", "暂无运行日志", "created_at", LocalDateTime.now().toString())) : rows;
        } catch (RuntimeException exception) {
            return List.of(SampleData.map("task_id", id, "level", "INFO", "message", "暂无运行日志", "created_at", LocalDateTime.now().toString()));
        }
    }

    public Map<String, Object> status(String id) {
        Document document = findDocument(id);
        return SampleData.map("id", id, "status", document.getString("status"), "lastSync", document.get("lastSync"), "updated_at", document.get("updated_at"));
    }

    private Map<String, Object> changeStatus(String id, String status, String message, HttpServletRequest request) {
        Document document = findDocument(id);
        document.put("status", status);
        document.put("updated_at", LocalDateTime.now());
        mongoTemplate.save(document, "task_records");
        writeLog(id, status, message);
        auditLogService.record("task." + status, "task_records", id, authService.requireCurrentUser().getId(), clientIp(request));
        return mapper.toMap(document);
    }

    private Document findDocument(String id) {
        Document document = mongoTemplate.findOne(Query.query(Criteria.where("_id").is(id)), Document.class, "task_records");
        if (document == null) {
            throw new BusinessException(HttpStatus.NOT_FOUND, "采集任务不存在");
        }
        return document;
    }

    private void writeLog(String taskId, String action, String message) {
        mongoTemplate.insert(new Document("task_id", taskId).append("action", action).append("level", "INFO").append("message", message).append("created_at", LocalDateTime.now()), "task_logs");
    }

    private String clientIp(HttpServletRequest request) {
        String forwarded = request.getHeader("X-Forwarded-For");
        return StringUtils.hasText(forwarded) ? forwarded.split(",")[0].trim() : request.getRemoteAddr();
    }
}