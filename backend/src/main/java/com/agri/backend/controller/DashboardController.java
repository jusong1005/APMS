package com.agri.backend.controller;

import com.agri.backend.dto.ApiResponse;
import com.agri.backend.service.DashboardService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/dashboard")
public class DashboardController {
    private final DashboardService dashboardService;

    public DashboardController(DashboardService dashboardService) {
        this.dashboardService = dashboardService;
    }

    @GetMapping("/overview")
    public ApiResponse<Map<String, Object>> overview() {
        return ApiResponse.ok(dashboardService.overview());
    }

    @GetMapping("/realtime")
    public ApiResponse<Map<String, Object>> realtime() {
        return ApiResponse.ok(dashboardService.realtime());
    }

    @GetMapping("/trend")
    public ApiResponse<List<Map<String, Object>>> trend(@RequestParam(required = false) String product, @RequestParam(required = false) String region) {
        return ApiResponse.ok(dashboardService.trend(product, region));
    }

    @GetMapping("/alerts")
    public ApiResponse<List<Map<String, Object>>> alerts() {
        return ApiResponse.ok(dashboardService.alerts());
    }
}