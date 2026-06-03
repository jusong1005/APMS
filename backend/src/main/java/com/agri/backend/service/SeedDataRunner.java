package com.agri.backend.service;

import com.agri.backend.domain.UserAccount;
import com.agri.backend.repository.UserAccountRepository;
import com.agri.backend.security.PermissionCatalog;
import java.time.LocalDateTime;
import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
public class SeedDataRunner implements ApplicationRunner {
    private static final Logger log = LoggerFactory.getLogger(SeedDataRunner.class);
    private final UserAccountRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final MongoTemplate mongoTemplate;

    public SeedDataRunner(UserAccountRepository userRepository, PasswordEncoder passwordEncoder, MongoTemplate mongoTemplate) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.mongoTemplate = mongoTemplate;
    }

    @Override
    public void run(ApplicationArguments args) {
        try {
            seedAdmin();
            seedDocuments();
        } catch (RuntimeException exception) {
            log.warn("Skip backend seed data because MongoDB is unavailable or not writable: {}", exception.getMessage());
        }
    }

    private void seedAdmin() {
        if (userRepository.count() > 0) {
            return;
        }
        LocalDateTime now = LocalDateTime.now();
        UserAccount admin = new UserAccount();
        admin.setAccount("admin");
        admin.setPasswordHash(passwordEncoder.encode("Agri@123456"));
        admin.setName("平台管理员");
        admin.setRole("admin");
        admin.setOrganization("农产品价格监测中心");
        admin.setPermissions(PermissionCatalog.permissionsForRole("admin"));
        admin.setActive(true);
        admin.setCreatedAt(now);
        admin.setUpdatedAt(now);
        userRepository.save(admin);
        log.info("Seeded default admin account: admin / Agri@123456");
    }

    private void seedDocuments() {
        if (mongoTemplate.getCollection("task_records").countDocuments() == 0) {
            SampleData.tasks().forEach(item -> mongoTemplate.insert(new Document(item).append("_id", item.get("id")).append("created_at", LocalDateTime.now()), "task_records"));
        }
        if (mongoTemplate.getCollection("alert_records").countDocuments() == 0) {
            SampleData.latestAlerts().forEach(item -> mongoTemplate.insert(new Document(item).append("_id", item.get("id")), "alert_records"));
        }
        if (mongoTemplate.getCollection("system_settings").countDocuments() == 0) {
            SampleData.settings().forEach((key, value) -> mongoTemplate.insert(new Document("key", key).append("value", value).append("updated_at", LocalDateTime.now()), "system_settings"));
        }
        if (mongoTemplate.getCollection("prediction_results").countDocuments() == 0) {
            SampleData.predictions().forEach(item -> mongoTemplate.insert(new Document(item).append("_id", item.get("product")), "prediction_results"));
        }
    }
}