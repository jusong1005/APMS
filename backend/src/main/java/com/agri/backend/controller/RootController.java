package com.agri.backend.controller;

import com.agri.backend.dto.ApiResponse;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RootController {
    @GetMapping({"/", "/api"})
    public ApiResponse<Map<String, Object>> index() {
        return ApiResponse.ok(Map.of(
            "name", "AgriPulse 农产品价格监控平台后端",
            "status", "running",
            "time", LocalDateTime.now().toString(),
            "health", "/actuator/health",
            "auth", "/api/auth/login",
            "docs", "backend/API.md",
            "publicEndpoints", List.of("/", "/api", "/actuator/health")
        ));
    }
}