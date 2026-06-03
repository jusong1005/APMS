package com.agri.backend.controller;

import com.agri.backend.dto.ApiResponse;
import com.agri.backend.dto.AuthDtos;
import com.agri.backend.dto.UserDtos;
import com.agri.backend.service.UserAdminService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class UserController {
    private final UserAdminService userAdminService;

    public UserController(UserAdminService userAdminService) {
        this.userAdminService = userAdminService;
    }

    @GetMapping("/api/users")
    public ApiResponse<List<AuthDtos.UserView>> users() {
        return ApiResponse.ok(userAdminService.list());
    }

    @PostMapping("/api/users")
    public ApiResponse<AuthDtos.UserView> create(@Valid @RequestBody UserDtos.UpsertUserRequest request, HttpServletRequest servletRequest) {
        return ApiResponse.ok("用户已创建", userAdminService.create(request, servletRequest));
    }

    @PutMapping("/api/users/{id}")
    public ApiResponse<AuthDtos.UserView> update(@PathVariable String id, @Valid @RequestBody UserDtos.UpsertUserRequest request, HttpServletRequest servletRequest) {
        return ApiResponse.ok("用户已更新", userAdminService.update(id, request, servletRequest));
    }

    @DeleteMapping("/api/users/{id}")
    public ApiResponse<Void> delete(@PathVariable String id, HttpServletRequest servletRequest) {
        userAdminService.delete(id, servletRequest);
        return ApiResponse.ok("用户已删除", null);
    }

    @PutMapping("/api/users/{id}/role")
    public ApiResponse<AuthDtos.UserView> role(@PathVariable String id, @Valid @RequestBody UserDtos.RoleChangeRequest request, HttpServletRequest servletRequest) {
        return ApiResponse.ok(userAdminService.changeRole(id, request, servletRequest));
    }

    @PutMapping("/api/users/{id}/status")
    public ApiResponse<AuthDtos.UserView> status(@PathVariable String id, @RequestBody UserDtos.StatusRequest request, HttpServletRequest servletRequest) {
        return ApiResponse.ok(userAdminService.changeStatus(id, request, servletRequest));
    }

    @PostMapping("/api/users/{id}/reset-password")
    public ApiResponse<Void> resetPassword(@PathVariable String id, @RequestBody UserDtos.ResetPasswordRequest request, HttpServletRequest servletRequest) {
        userAdminService.resetPassword(id, request, servletRequest);
        return ApiResponse.ok("密码已重置", null);
    }

    @GetMapping("/api/roles")
    public ApiResponse<List<Map<String, Object>>> roles() {
        return ApiResponse.ok(userAdminService.roles());
    }

    @GetMapping("/api/permissions")
    public ApiResponse<List<String>> permissions() {
        return ApiResponse.ok(userAdminService.permissions());
    }
}