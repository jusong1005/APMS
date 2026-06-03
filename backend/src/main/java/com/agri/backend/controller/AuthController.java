package com.agri.backend.controller;

import com.agri.backend.dto.ApiResponse;
import com.agri.backend.dto.AuthDtos;
import com.agri.backend.service.AuthService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/register")
    public ApiResponse<AuthDtos.UserView> register(@Valid @RequestBody AuthDtos.RegisterRequest request, HttpServletRequest servletRequest) {
        return ApiResponse.ok("注册成功", authService.register(request, servletRequest));
    }

    @PostMapping("/login")
    public ApiResponse<AuthDtos.AuthResponse> login(@Valid @RequestBody AuthDtos.LoginRequest request, HttpServletRequest servletRequest) {
        return ApiResponse.ok("登录成功", authService.login(request, servletRequest));
    }

    @PostMapping("/logout")
    public ApiResponse<Void> logout(@RequestBody(required = false) AuthDtos.LogoutRequest request, HttpServletRequest servletRequest) {
        authService.logout(request == null ? null : request.refreshToken(), servletRequest);
        return ApiResponse.ok("已退出登录", null);
    }

    @PostMapping("/refresh-token")
    public ApiResponse<AuthDtos.AuthResponse> refreshToken(@Valid @RequestBody AuthDtos.TokenRefreshRequest request) {
        return ApiResponse.ok(authService.refresh(request.refreshToken()));
    }

    @GetMapping("/me")
    public ApiResponse<AuthDtos.UserView> me() {
        return ApiResponse.ok(authService.me());
    }

    @PutMapping("/password")
    public ApiResponse<Void> changePassword(@Valid @RequestBody AuthDtos.ChangePasswordRequest request, HttpServletRequest servletRequest) {
        authService.changePassword(request, servletRequest);
        return ApiResponse.ok("密码已修改，请重新登录", null);
    }

    @PostMapping("/send-code")
    public ApiResponse<Map<String, Object>> sendCode(@Valid @RequestBody AuthDtos.SendCodeRequest request, HttpServletRequest servletRequest) {
        return ApiResponse.ok("验证码已生成", authService.sendPasswordResetCode(request, servletRequest));
    }

    @PostMapping("/forgot-password")
    public ApiResponse<Map<String, Object>> forgotPassword(@Valid @RequestBody AuthDtos.ResetPasswordRequest request, HttpServletRequest servletRequest) {
        authService.resetPassword(request, servletRequest);
        return ApiResponse.ok("密码已重置，请重新登录", Map.of("status", "reset"));
    }

    @PostMapping("/reset-password")
    public ApiResponse<Map<String, Object>> resetPassword(@Valid @RequestBody AuthDtos.ResetPasswordRequest request, HttpServletRequest servletRequest) {
        authService.resetPassword(request, servletRequest);
        return ApiResponse.ok("密码已重置，请重新登录", Map.of("status", "reset"));
    }
}