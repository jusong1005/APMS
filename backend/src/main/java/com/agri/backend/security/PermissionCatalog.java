package com.agri.backend.security;

import com.agri.backend.domain.UserAccount;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.springframework.security.core.authority.SimpleGrantedAuthority;

public final class PermissionCatalog {
    private static final Map<String, List<String>> ROLE_PERMISSIONS = Map.of(
        "admin", List.of("dashboard:read", "analysis:read", "alerts:read", "alerts:write", "tasks:write", "users:write", "settings:write", "profile:write", "export:run", "predictions:write"),
        "analyst", List.of("dashboard:read", "analysis:read", "alerts:read", "alerts:write", "tasks:write", "profile:write", "export:run", "predictions:read"),
        "user", List.of("dashboard:read", "analysis:read", "alerts:read", "profile:write", "predictions:read")
    );

    private PermissionCatalog() {
    }

    public static String normalizeRole(String role) {
        if (role == null || role.isBlank()) {
            return "user";
        }
        String normalized = role.trim().toLowerCase(Locale.ROOT);
        return ROLE_PERMISSIONS.containsKey(normalized) ? normalized : "user";
    }

    public static List<String> permissionsForRole(String role) {
        return ROLE_PERMISSIONS.getOrDefault(normalizeRole(role), ROLE_PERMISSIONS.get("user"));
    }

    public static List<Map<String, Object>> roles() {
        return List.of(
            Map.of("key", "admin", "name", "管理员", "description", "管理用户、任务、系统配置和全部业务数据"),
            Map.of("key", "analyst", "name", "数据分析员", "description", "运行任务、导出分析结果并处理预警"),
            Map.of("key", "user", "name", "普通用户", "description", "查看监控、分析、预测和预警结果")
        );
    }

    public static List<String> allPermissions() {
        return ROLE_PERMISSIONS.values().stream().flatMap(List::stream).distinct().sorted().toList();
    }

    public static List<SimpleGrantedAuthority> authoritiesFor(UserAccount user) {
        List<SimpleGrantedAuthority> authorities = new ArrayList<>();
        String role = normalizeRole(user.getRole());
        authorities.add(new SimpleGrantedAuthority("ROLE_" + role.toUpperCase(Locale.ROOT)));
        permissionsForRole(role).forEach(permission -> authorities.add(new SimpleGrantedAuthority(permission)));
        return authorities;
    }
}