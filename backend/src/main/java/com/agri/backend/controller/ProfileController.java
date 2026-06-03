package com.agri.backend.controller;

import com.agri.backend.dto.ApiResponse;
import com.agri.backend.dto.AuthDtos;
import com.agri.backend.service.AuthService;
import com.agri.backend.service.SettingsService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/profile")
public class ProfileController {
    private final SettingsService settingsService;
    private final AuthService authService;

    public ProfileController(SettingsService settingsService, AuthService authService) {
        this.settingsService = settingsService;
        this.authService = authService;
    }

    @GetMapping
    public ApiResponse<AuthDtos.UserView> profile() {
        return ApiResponse.ok(settingsService.profile());
    }

    @PutMapping
    public ApiResponse<AuthDtos.UserView> updateProfile(@RequestBody Map<String, Object> body, HttpServletRequest request) {
        return ApiResponse.ok("个人资料已保存", settingsService.updateProfile(body, request));
    }

    @PostMapping("/password")
    public ApiResponse<Void> password(@Valid @RequestBody AuthDtos.ChangePasswordRequest request, HttpServletRequest servletRequest) {
        authService.changePassword(request, servletRequest);
        return ApiResponse.ok("密码已修改", null);
    }

    @PostMapping("/avatar")
    public ApiResponse<Map<String, Object>> avatar(@RequestPart("file") MultipartFile file, HttpServletRequest request) {
        return ApiResponse.ok("头像已上传", settingsService.uploadAvatar(file, request));
    }

    @PutMapping("/preferences")
    public ApiResponse<Map<String, Object>> preferences(@RequestBody Map<String, Object> body, HttpServletRequest request) {
        return ApiResponse.ok("偏好设置已保存", settingsService.savePreferences(body, request));
    }
}