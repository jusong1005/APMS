package com.agri.backend.controller;

import com.agri.backend.dto.ApiResponse;
import com.agri.backend.service.TaskService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/tasks")
public class TaskController {
    private final TaskService taskService;

    public TaskController(TaskService taskService) {
        this.taskService = taskService;
    }

    @GetMapping
    public ApiResponse<List<Map<String, Object>>> list(@RequestParam(defaultValue = "all") String status, @RequestParam(required = false) String keyword) {
        return ApiResponse.ok(taskService.list(status, keyword));
    }

    @PostMapping
    public ApiResponse<Map<String, Object>> create(@RequestBody Map<String, Object> body, HttpServletRequest request) {
        return ApiResponse.ok("采集任务已创建", taskService.create(body, request));
    }

    @PutMapping("/{id}")
    public ApiResponse<Map<String, Object>> update(@PathVariable String id, @RequestBody Map<String, Object> body, HttpServletRequest request) {
        return ApiResponse.ok("采集任务已更新", taskService.update(id, body, request));
    }

    @PostMapping("/{id}/start")
    public ApiResponse<Map<String, Object>> start(@PathVariable String id, HttpServletRequest request) {
        return ApiResponse.ok("采集任务已启动", taskService.start(id, request));
    }

    @PostMapping("/{id}/stop")
    public ApiResponse<Map<String, Object>> stop(@PathVariable String id, HttpServletRequest request) {
        return ApiResponse.ok("采集任务已停止", taskService.stop(id, request));
    }

    @GetMapping("/{id}/logs")
    public ApiResponse<List<Map<String, Object>>> logs(@PathVariable String id) {
        return ApiResponse.ok(taskService.logs(id));
    }

    @GetMapping("/{id}/status")
    public ApiResponse<Map<String, Object>> status(@PathVariable String id) {
        return ApiResponse.ok(taskService.status(id));
    }
}