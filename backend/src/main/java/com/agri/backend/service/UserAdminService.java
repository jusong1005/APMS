package com.agri.backend.service;

import com.agri.backend.domain.UserAccount;
import com.agri.backend.dto.AuthDtos;
import com.agri.backend.dto.UserDtos;
import com.agri.backend.exception.BusinessException;
import com.agri.backend.repository.UserAccountRepository;
import com.agri.backend.security.PermissionCatalog;
import jakarta.servlet.http.HttpServletRequest;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
public class UserAdminService {
    private final UserAccountRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuthService authService;
    private final AuditLogService auditLogService;

    public UserAdminService(UserAccountRepository userRepository, PasswordEncoder passwordEncoder, AuthService authService, AuditLogService auditLogService) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.authService = authService;
        this.auditLogService = auditLogService;
    }

    public List<AuthDtos.UserView> list() {
        return userRepository.findAll(Sort.by(Sort.Direction.DESC, "createdAt")).stream().map(AuthDtos.UserView::from).toList();
    }

    public AuthDtos.UserView create(UserDtos.UpsertUserRequest request, HttpServletRequest servletRequest) {
        if (userRepository.existsByAccount(request.account().trim())) {
            throw new BusinessException(HttpStatus.CONFLICT, "账号已存在");
        }
        LocalDateTime now = LocalDateTime.now();
        UserAccount user = new UserAccount();
        user.setAccount(request.account().trim());
        user.setPasswordHash(passwordEncoder.encode(StringUtils.hasText(request.password()) ? request.password() : "Agri@123456"));
        applyEditableFields(user, request);
        user.setCreatedAt(now);
        user.setUpdatedAt(now);
        UserAccount saved = userRepository.save(user);
        audit("user.create", saved.getId(), servletRequest);
        return AuthDtos.UserView.from(saved);
    }

    public AuthDtos.UserView update(String id, UserDtos.UpsertUserRequest request, HttpServletRequest servletRequest) {
        UserAccount user = findUser(id);
        if (!user.getAccount().equals(request.account().trim()) && userRepository.existsByAccount(request.account().trim())) {
            throw new BusinessException(HttpStatus.CONFLICT, "账号已存在");
        }
        user.setAccount(request.account().trim());
        if (StringUtils.hasText(request.password())) {
            user.setPasswordHash(passwordEncoder.encode(request.password()));
        }
        applyEditableFields(user, request);
        user.setUpdatedAt(LocalDateTime.now());
        UserAccount saved = userRepository.save(user);
        audit("user.update", saved.getId(), servletRequest);
        return AuthDtos.UserView.from(saved);
    }

    public void delete(String id, HttpServletRequest servletRequest) {
        UserAccount current = authService.requireCurrentUser();
        if (current.getId().equals(id)) {
            throw new BusinessException(HttpStatus.BAD_REQUEST, "不能删除当前登录账号");
        }
        userRepository.deleteById(id);
        audit("user.delete", id, servletRequest);
    }

    public AuthDtos.UserView changeRole(String id, UserDtos.RoleChangeRequest request, HttpServletRequest servletRequest) {
        UserAccount user = findUser(id);
        String role = PermissionCatalog.normalizeRole(request.role());
        user.setRole(role);
        user.setPermissions(PermissionCatalog.permissionsForRole(role));
        user.setUpdatedAt(LocalDateTime.now());
        UserAccount saved = userRepository.save(user);
        audit("user.role", id, servletRequest);
        return AuthDtos.UserView.from(saved);
    }

    public AuthDtos.UserView changeStatus(String id, UserDtos.StatusRequest request, HttpServletRequest servletRequest) {
        UserAccount user = findUser(id);
        user.setActive(Boolean.TRUE.equals(request.active()));
        user.setUpdatedAt(LocalDateTime.now());
        UserAccount saved = userRepository.save(user);
        audit("user.status", id, servletRequest);
        return AuthDtos.UserView.from(saved);
    }

    public void resetPassword(String id, UserDtos.ResetPasswordRequest request, HttpServletRequest servletRequest) {
        UserAccount user = findUser(id);
        String password = StringUtils.hasText(request.password()) ? request.password() : "Agri@123456";
        user.setPasswordHash(passwordEncoder.encode(password));
        user.setUpdatedAt(LocalDateTime.now());
        userRepository.save(user);
        audit("user.password.reset", id, servletRequest);
    }

    public List<Map<String, Object>> roles() {
        return PermissionCatalog.roles();
    }

    public List<String> permissions() {
        return PermissionCatalog.allPermissions();
    }

    private void applyEditableFields(UserAccount user, UserDtos.UpsertUserRequest request) {
        user.setName(request.name().trim());
        user.setPhone(trimToNull(request.phone()));
        user.setEmail(trimToNull(request.email()));
        user.setOrganization(trimToNull(request.organization()));
        String role = PermissionCatalog.normalizeRole(request.role());
        user.setRole(role);
        user.setPermissions(PermissionCatalog.permissionsForRole(role));
        user.setActive(request.active() == null || request.active());
    }

    private UserAccount findUser(String id) {
        return userRepository.findById(id).orElseThrow(() -> new BusinessException(HttpStatus.NOT_FOUND, "用户不存在"));
    }

    private String trimToNull(String value) {
        return StringUtils.hasText(value) ? value.trim() : null;
    }

    private void audit(String action, String target, HttpServletRequest request) {
        auditLogService.record(action, "user_accounts", target, authService.requireCurrentUser().getId(), request.getRemoteAddr());
    }
}