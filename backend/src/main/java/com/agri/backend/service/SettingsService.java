package com.agri.backend.service;

import com.agri.backend.domain.UserAccount;
import com.agri.backend.dto.AuthDtos;
import com.agri.backend.exception.BusinessException;
import jakarta.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.bson.Document;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Sort;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import org.springframework.data.redis.connection.RedisConnection;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Service
public class SettingsService {
    private final MongoTemplate mongoTemplate;
    private final StringRedisTemplate redisTemplate;
    private final MongoDocumentMapper mapper;
    private final AuthService authService;
    private final AuditLogService auditLogService;
    private final Path uploadDir;

    public SettingsService(
        MongoTemplate mongoTemplate,
        StringRedisTemplate redisTemplate,
        MongoDocumentMapper mapper,
        AuthService authService,
        AuditLogService auditLogService,
        @Value("${app.files.upload-dir}") String uploadDir
    ) {
        this.mongoTemplate = mongoTemplate;
        this.redisTemplate = redisTemplate;
        this.mapper = mapper;
        this.authService = authService;
        this.auditLogService = auditLogService;
        this.uploadDir = Path.of(uploadDir);
    }

    public Map<String, Object> settings() {
        List<Document> docs = mongoTemplate.findAll(Document.class, "system_settings");
        if (docs.isEmpty()) {
            return SampleData.settings();
        }
        Map<String, Object> result = new LinkedHashMap<>();
        docs.forEach(document -> result.put(document.getString("key"), document.get("value")));
        return result;
    }

    public Map<String, Object> saveSettings(Map<String, Object> settings, HttpServletRequest request) {
        settings.forEach((key, value) -> mongoTemplate.upsert(
            Query.query(Criteria.where("key").is(key)),
            new Update().set("value", value).set("updated_at", LocalDateTime.now()).set("updated_by", authService.requireCurrentUser().getId()),
            "system_settings"
        ));
        auditLogService.record("settings.update", "system_settings", settings.keySet().toString(), authService.requireCurrentUser().getId(), request.getRemoteAddr());
        return settings();
    }

    public Map<String, Object> dbStatus() {
        return SampleData.map(
            "mongodb", mongoStatus(),
            "redis", redisStatus(),
            "kafka", SampleData.map("status", "not_checked", "message", "Kafka 由采集和 Spark 链路直接使用"),
            "checkedAt", LocalDateTime.now().toString()
        );
    }

    public List<Map<String, Object>> auditLogs() {
        Query query = new Query().with(Sort.by(Sort.Direction.DESC, "created_at")).limit(100);
        List<Map<String, Object>> rows = mapper.toMaps(mongoTemplate.find(query, Document.class, "audit_logs"));
        return rows.isEmpty() ? List.of(SampleData.map("action", "system.demo", "target", "audit_logs", "detail", "暂无审计日志", "created_at", LocalDateTime.now().toString())) : rows;
    }

    public AuthDtos.UserView profile() {
        return AuthDtos.UserView.from(authService.requireCurrentUser());
    }

    public AuthDtos.UserView updateProfile(Map<String, Object> body, HttpServletRequest request) {
        UserAccount user = authService.requireCurrentUser();
        if (body.containsKey("name")) {
            user.setName(String.valueOf(body.get("name")));
        }
        if (body.containsKey("phone")) {
            user.setPhone(String.valueOf(body.get("phone")));
        }
        if (body.containsKey("email")) {
            user.setEmail(String.valueOf(body.get("email")));
        }
        if (body.containsKey("organization")) {
            user.setOrganization(String.valueOf(body.get("organization")));
        }
        user.setUpdatedAt(LocalDateTime.now());
        mongoTemplate.save(user);
        auditLogService.record("profile.update", "user_accounts", user.getAccount(), user.getId(), request.getRemoteAddr());
        return AuthDtos.UserView.from(user);
    }

    public Map<String, Object> savePreferences(Map<String, Object> preferences, HttpServletRequest request) {
        UserAccount user = authService.requireCurrentUser();
        user.setPreferences(preferences);
        user.setUpdatedAt(LocalDateTime.now());
        mongoTemplate.save(user);
        auditLogService.record("profile.preferences", "user_accounts", user.getAccount(), user.getId(), request.getRemoteAddr());
        return preferences;
    }

    public Map<String, Object> uploadAvatar(MultipartFile file, HttpServletRequest request) {
        if (file == null || file.isEmpty()) {
            throw new BusinessException(HttpStatus.BAD_REQUEST, "请选择头像文件");
        }
        try {
            UserAccount user = authService.requireCurrentUser();
            Path avatarDir = uploadDir.resolve("avatars");
            Files.createDirectories(avatarDir);
            String original = file.getOriginalFilename() == null ? "avatar" : file.getOriginalFilename().replaceAll("[^a-zA-Z0-9._-]", "_");
            String fileName = user.getId() + "-" + System.currentTimeMillis() + "-" + original;
            Path target = avatarDir.resolve(fileName);
            file.transferTo(target);
            String avatarUrl = "/uploads/avatars/" + fileName;
            user.setAvatarUrl(avatarUrl);
            user.setUpdatedAt(LocalDateTime.now());
            mongoTemplate.save(user);
            auditLogService.record("profile.avatar", "user_accounts", user.getAccount(), user.getId(), request.getRemoteAddr());
            return SampleData.map("avatarUrl", avatarUrl);
        } catch (IOException exception) {
            throw new BusinessException(HttpStatus.INTERNAL_SERVER_ERROR, "头像保存失败");
        }
    }

    private Map<String, Object> mongoStatus() {
        try {
            Document result = mongoTemplate.executeCommand(new Document("ping", 1));
            return SampleData.map("status", "up", "detail", mapper.toMap(result));
        } catch (RuntimeException exception) {
            return SampleData.map("status", "down", "message", exception.getMessage());
        }
    }

    private Map<String, Object> redisStatus() {
        try (RedisConnection connection = redisTemplate.getConnectionFactory().getConnection()) {
            return SampleData.map("status", "up", "detail", connection.ping());
        } catch (RuntimeException exception) {
            return SampleData.map("status", "down", "message", exception.getMessage());
        }
    }
}