package com.agri.backend.controller;

import com.agri.backend.dto.ApiResponse;
import com.agri.backend.service.SettingsService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class SettingsController {
    private final SettingsService settingsService;

    public SettingsController(SettingsService settingsService) {
        this.settingsService = settingsService;
    }

    @GetMapping("/api/settings")
    public ApiResponse<Map<String, Object>> settings() {
        return ApiResponse.ok(settingsService.settings());
    }

    @PutMapping("/api/settings")
    public ApiResponse<Map<String, Object>> saveSettings(@RequestBody Map<String, Object> body, HttpServletRequest request) {
        return ApiResponse.ok("系统配置已保存", settingsService.saveSettings(body, request));
    }

    @GetMapping("/api/settings/db-status")
    public ApiResponse<Map<String, Object>> dbStatus() {
        return ApiResponse.ok(settingsService.dbStatus());
    }

    @GetMapping("/api/audit-logs")
    public ApiResponse<List<Map<String, Object>>> auditLogs() {
        return ApiResponse.ok(settingsService.auditLogs());
    }
}