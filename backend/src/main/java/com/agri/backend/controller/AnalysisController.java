package com.agri.backend.controller;

import com.agri.backend.dto.ApiResponse;
import com.agri.backend.service.AnalysisService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/analysis")
public class AnalysisController {
    private final AnalysisService analysisService;

    public AnalysisController(AnalysisService analysisService) {
        this.analysisService = analysisService;
    }

    @GetMapping("/overview")
    public ApiResponse<Map<String, Object>> overview() {
        return ApiResponse.ok(analysisService.overview());
    }

    @GetMapping("/product-statistics")
    public ApiResponse<List<Map<String, Object>>> productStatistics() {
        return ApiResponse.ok(analysisService.productStatistics());
    }

    @GetMapping("/region-statistics")
    public ApiResponse<List<Map<String, Object>>> regionStatistics() {
        return ApiResponse.ok(analysisService.regionStatistics());
    }

    @GetMapping("/region-price-difference")
    public ApiResponse<List<Map<String, Object>>> regionPriceDifference() {
        return ApiResponse.ok(analysisService.regionPriceDifference());
    }

    @GetMapping("/yearly-trend")
    public ApiResponse<List<Map<String, Object>>> yearlyTrend() {
        return ApiResponse.ok(analysisService.yearlyTrend());
    }

    @GetMapping("/daily-trend")
    public ApiResponse<List<Map<String, Object>>> dailyTrend() {
        return ApiResponse.ok(analysisService.dailyTrend());
    }

    @GetMapping("/seasonal-price-change")
    public ApiResponse<List<Map<String, Object>>> seasonalPriceChange() {
        return ApiResponse.ok(analysisService.seasonalPriceChange());
    }

    @GetMapping("/price-range-analysis")
    public ApiResponse<List<Map<String, Object>>> priceRangeAnalysis() {
        return ApiResponse.ok(analysisService.priceRangeAnalysis());
    }

    @GetMapping("/volatility")
    public ApiResponse<List<Map<String, Object>>> volatility() {
        return ApiResponse.ok(analysisService.volatility());
    }

    @GetMapping("/weather-correlation")
    public ApiResponse<List<Map<String, Object>>> weatherCorrelation() {
        return ApiResponse.ok(analysisService.weatherCorrelation());
    }

    @GetMapping("/spark-sql")
    public ApiResponse<List<Map<String, Object>>> sparkSql() {
        return ApiResponse.ok(analysisService.sparkSql());
    }

    @GetMapping("/top-fluctuations")
    public ApiResponse<List<Map<String, Object>>> topFluctuations() {
        return ApiResponse.ok(analysisService.topFluctuations());
    }

    @GetMapping("/export")
    public ApiResponse<Map<String, Object>> export() {
        return ApiResponse.ok(analysisService.export());
    }
}