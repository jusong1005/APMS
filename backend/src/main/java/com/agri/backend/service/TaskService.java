package com.agri.backend.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.agri.backend.exception.BusinessException;
import jakarta.servlet.http.HttpServletRequest;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import org.springframework.beans.factory.annotation.Value;
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
    private static final DateTimeFormatter DISPLAY_TIME_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final List<String> DEFAULT_WEB_PRODUCTS = List.of("番茄", "大白菜", "黄瓜", "土豆", "玉米", "大米", "大豆", "猪肉", "牛肉", "鸡蛋");

    private final MongoTemplate mongoTemplate;
    private final MongoDocumentMapper mapper;
    private final AuthService authService;
    private final AuditLogService auditLogService;
    private final ObjectMapper objectMapper;
    private final String pythonBin;
    private final Path realtimeCollectorScript;
    private final Path importScript;
    private final Path outputDirectory;
    private final Duration collectorTimeout;
    private final String mongodbUri;

    public TaskService(
        MongoTemplate mongoTemplate,
        MongoDocumentMapper mapper,
        AuthService authService,
        AuditLogService auditLogService,
        ObjectMapper objectMapper,
        @Value("${app.collector.python-bin}") String pythonBin,
        @Value("${app.collector.realtime-script}") String realtimeCollectorScript,
        @Value("${app.collector.import-script}") String importScript,
        @Value("${app.collector.output-dir}") String outputDirectory,
        @Value("${app.collector.timeout-seconds}") long timeoutSeconds,
        @Value("${spring.data.mongodb.uri}") String mongodbUri
    ) {
        this.mongoTemplate = mongoTemplate;
        this.mapper = mapper;
        this.authService = authService;
        this.auditLogService = auditLogService;
        this.objectMapper = objectMapper;
        this.pythonBin = pythonBin;
        this.realtimeCollectorScript = Path.of(realtimeCollectorScript).toAbsolutePath().normalize();
        this.importScript = Path.of(importScript).toAbsolutePath().normalize();
        this.outputDirectory = Path.of(outputDirectory).toAbsolutePath().normalize();
        this.collectorTimeout = Duration.ofSeconds(timeoutSeconds);
        this.mongodbUri = mongodbUri;
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
        Document document = findDocument(id);
        document.put("status", "running");
        document.put("updated_at", LocalDateTime.now());
        mongoTemplate.save(document, "task_records");
        writeLog(id, "start", "INFO", "启动任务并执行一次网页采集");
        auditLogService.record("task.start", "task_records", id, authService.requireCurrentUser().getId(), clientIp(request));
        try {
            Map<String, Object> crawlSummary = runWebCrawler(document);
            LocalDateTime now = LocalDateTime.now();
            document.put("status", "running");
            document.put("lastSync", DISPLAY_TIME_FORMATTER.format(now));
            document.put("updated_at", now);
            document.put("successRate", 100);
            document.put("backlog", 0);
            document.put("lastCrawlSummary", crawlSummary);
            mongoTemplate.save(document, "task_records");
            writeLog(id, "crawl", "INFO", buildCrawlLogMessage(crawlSummary));
            return mapper.toMap(document);
        } catch (RuntimeException exception) {
            document.put("status", "error");
            document.put("updated_at", LocalDateTime.now());
            mongoTemplate.save(document, "task_records");
            writeLog(id, "crawl", "ERROR", "网页采集失败：" + exception.getMessage());
            throw new BusinessException(HttpStatus.INTERNAL_SERVER_ERROR, "网页采集失败：" + exception.getMessage());
        }
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
        writeLog(id, status, "INFO", message);
        auditLogService.record("task." + status, "task_records", id, authService.requireCurrentUser().getId(), clientIp(request));
        return mapper.toMap(document);
    }

    private Map<String, Object> runWebCrawler(Document task) {
        try {
            Files.createDirectories(outputDirectory);
            String taskId = String.valueOf(task.get("_id"));
            String runId = taskId.replaceAll("[^A-Za-z0-9_-]", "_") + "-" + System.currentTimeMillis();
            Path priceOutput = outputDirectory.resolve(runId + "-price.csv");
            Path weatherOutput = outputDirectory.resolve(runId + "-weather.csv");
            List<String> products = taskProducts(task);
            int lookbackDays = taskLookbackDays(task);

            List<String> collectCommand = new ArrayList<>();
            collectCommand.add(pythonBin);
            collectCommand.add(realtimeCollectorScript.toString());
            collectCommand.add("--lookback-days");
            collectCommand.add(String.valueOf(lookbackDays));
            collectCommand.add("--price-output");
            collectCommand.add(priceOutput.toString());
            collectCommand.add("--weather-output");
            collectCommand.add(weatherOutput.toString());
            collectCommand.add("--products");
            collectCommand.addAll(products);

            String collectorOutput = runProcess(collectCommand, realtimeCollectorScript.getParent());
            Map<String, Object> collectorSummary = parseJsonObject(collectorOutput);

            List<String> importCommand = List.of(
                pythonBin,
                importScript.toString(),
                "--mongodb-uri", mongodbUri,
                "--mongodb-database", mongoTemplate.getDb().getName(),
                "--price-csv", priceOutput.toString(),
                "--weather-csv", weatherOutput.toString(),
                "--source-topic", "realtime_web",
                "--batch-size", "1000"
            );
            String importOutput = runProcess(importCommand, importScript.getParent());
            Map<String, Object> importSummary = parseJsonObject(importOutput);

            Map<String, Object> summary = new LinkedHashMap<>();
            summary.put("products", products);
            summary.put("lookbackDays", lookbackDays);
            summary.put("collector", collectorSummary);
            summary.put("importer", importSummary);
            summary.put("priceOutput", priceOutput.toString());
            summary.put("weatherOutput", weatherOutput.toString());
            return summary;
        } catch (IOException | InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException(exception.getMessage(), exception);
        }
    }

    private String runProcess(List<String> command, Path workingDirectory) throws IOException, InterruptedException {
        ProcessBuilder processBuilder = new ProcessBuilder(command);
        processBuilder.directory(workingDirectory.toFile());
        processBuilder.redirectErrorStream(true);
        processBuilder.environment().put("PYTHONIOENCODING", "utf-8");
        Process process = processBuilder.start();
        StringBuilder output = new StringBuilder();
        Thread outputReader = new Thread(() -> readProcessOutput(process, output), "task-crawler-output-reader");
        outputReader.setDaemon(true);
        outputReader.start();
        boolean finished = process.waitFor(collectorTimeout.toSeconds(), TimeUnit.SECONDS);
        if (!finished) {
            process.destroyForcibly();
            throw new IllegalStateException("采集进程超时：" + collectorTimeout.toSeconds() + " 秒");
        }
        outputReader.join(1000);
        int exitCode = process.exitValue();
        if (exitCode != 0) {
            throw new IllegalStateException("采集进程退出码 " + exitCode + "，输出：" + abbreviate(output.toString(), 600));
        }
        return output.toString();
    }

    private void readProcessOutput(Process process, StringBuilder output) {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append(System.lineSeparator());
            }
        } catch (IOException exception) {
            output.append("\n[output-read-error] ").append(exception.getMessage());
        }
    }

    private Map<String, Object> parseJsonObject(String output) {
        int startIndex = output.indexOf('{');
        int endIndex = output.lastIndexOf('}');
        if (startIndex >= 0 && endIndex > startIndex) {
            try {
                return objectMapper.readValue(output.substring(startIndex, endIndex + 1), new TypeReference<>() {
                });
            } catch (IOException ignored) {
            }
        }
        return SampleData.map("rawOutput", abbreviate(output, 1000));
    }

    private List<String> taskProducts(Document task) {
        Object productsValue = task.get("products");
        LinkedHashSet<String> products = new LinkedHashSet<>();
        if (productsValue instanceof List<?> list) {
            list.stream().map(String::valueOf).map(String::trim).filter(StringUtils::hasText).forEach(products::add);
        } else if (productsValue != null && StringUtils.hasText(String.valueOf(productsValue))) {
            Arrays.stream(String.valueOf(productsValue).split("[,，\\s]+"))
                .map(String::trim)
                .filter(StringUtils::hasText)
                .forEach(products::add);
        }
        if (products.isEmpty()) {
            products.addAll(DEFAULT_WEB_PRODUCTS);
        }
        return List.copyOf(products);
    }

    private int taskLookbackDays(Document task) {
        Object value = task.getOrDefault("lookbackDays", task.getOrDefault("lookback_days", 3));
        try {
            return Math.max(1, Math.min(30, Integer.parseInt(String.valueOf(value))));
        } catch (NumberFormatException exception) {
            return 3;
        }
    }

    @SuppressWarnings("unchecked")
    private String buildCrawlLogMessage(Map<String, Object> crawlSummary) {
        Map<String, Object> collector = crawlSummary.get("collector") instanceof Map<?, ?> map ? (Map<String, Object>) map : Map.of();
        Map<String, Object> importer = crawlSummary.get("importer") instanceof Map<?, ?> map ? (Map<String, Object>) map : Map.of();
        return "网页采集完成：价格样本 " + collector.getOrDefault("price_records", 0)
            + " 条，天气样本 " + collector.getOrDefault("weather_records", 0)
            + " 条；入库结果 " + importer;
    }

    private String abbreviate(String value, int maxLength) {
        if (value == null || value.length() <= maxLength) {
            return value;
        }
        return value.substring(0, maxLength) + "...";
    }

    private Document findDocument(String id) {
        Document document = mongoTemplate.findOne(Query.query(Criteria.where("_id").is(id)), Document.class, "task_records");
        if (document == null) {
            throw new BusinessException(HttpStatus.NOT_FOUND, "采集任务不存在");
        }
        return document;
    }

    private void writeLog(String taskId, String action, String message) {
        writeLog(taskId, action, "INFO", message);
    }

    private void writeLog(String taskId, String action, String level, String message) {
        mongoTemplate.insert(new Document("task_id", taskId).append("action", action).append("level", level).append("message", message).append("created_at", LocalDateTime.now()), "task_logs");
    }

    private String clientIp(HttpServletRequest request) {
        String forwarded = request.getHeader("X-Forwarded-For");
        return StringUtils.hasText(forwarded) ? forwarded.split(",")[0].trim() : request.getRemoteAddr();
    }
}