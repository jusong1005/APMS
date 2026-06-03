package com.agri.backend.controller;

import com.agri.backend.dto.ApiResponse;
import com.agri.backend.service.AlertService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/alerts")
public class AlertController {
    private final AlertService alertService;

    public AlertController(AlertService alertService) {
        this.alertService = alertService;
    }

    @GetMapping("/rules")
    public ApiResponse<List<Map<String, Object>>> rules() {
        return ApiResponse.ok(alertService.rules());
    }

    @PostMapping("/rules")
    public ApiResponse<Map<String, Object>> createRule(@RequestBody Map<String, Object> body, HttpServletRequest request) {
        return ApiResponse.ok("预警规则已创建", alertService.createRule(body, request));
    }

    @PutMapping("/rules/{id}")
    public ApiResponse<Map<String, Object>> updateRule(@PathVariable String id, @RequestBody Map<String, Object> body, HttpServletRequest request) {
        return ApiResponse.ok("预警规则已更新", alertService.updateRule(id, body, request));
    }

    @DeleteMapping("/rules/{id}")
    public ApiResponse<Void> deleteRule(@PathVariable String id, HttpServletRequest request) {
        alertService.deleteRule(id, request);
        return ApiResponse.ok("预警规则已删除", null);
    }

    @GetMapping("/records")
    public ApiResponse<List<Map<String, Object>>> records(@RequestParam(defaultValue = "all") String status) {
        return ApiResponse.ok(alertService.records(status));
    }

    @PutMapping("/records/{id}/ack")
    public ApiResponse<Map<String, Object>> ack(@PathVariable String id, HttpServletRequest request) {
        return ApiResponse.ok("预警已确认", alertService.ack(id, request));
    }

    @PutMapping("/records/{id}/close")
    public ApiResponse<Map<String, Object>> close(@PathVariable String id, HttpServletRequest request) {
        return ApiResponse.ok("预警已关闭", alertService.close(id, request));
    }
}