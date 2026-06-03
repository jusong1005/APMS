package com.agri.backend.controller;

import com.agri.backend.dto.ApiResponse;
import com.agri.backend.service.PredictionService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/predictions")
public class PredictionController {
    private final PredictionService predictionService;

    public PredictionController(PredictionService predictionService) {
        this.predictionService = predictionService;
    }

    @GetMapping
    public ApiResponse<List<Map<String, Object>>> list() {
        return ApiResponse.ok(predictionService.list());
    }

    @GetMapping("/{product}")
    public ApiResponse<Map<String, Object>> detail(@PathVariable String product) {
        return ApiResponse.ok(predictionService.detail(product));
    }

    @GetMapping("/{product}/factors")
    public ApiResponse<Map<String, Object>> factors(@PathVariable String product) {
        return ApiResponse.ok(predictionService.factors(product));
    }

    @PostMapping("/refresh")
    public ApiResponse<Map<String, Object>> refresh(HttpServletRequest request) {
        return ApiResponse.ok(predictionService.refresh(request));
    }
}