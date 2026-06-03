package com.agri.backend.service;

import com.agri.backend.config.JwtProperties;
import com.agri.backend.domain.LoginSession;
import com.agri.backend.domain.UserAccount;
import com.agri.backend.dto.AuthDtos;
import com.agri.backend.exception.BusinessException;
import com.agri.backend.repository.LoginSessionRepository;
import com.agri.backend.repository.UserAccountRepository;
import com.agri.backend.security.JwtService;
import com.agri.backend.security.PermissionCatalog;
import io.jsonwebtoken.JwtException;
import jakarta.servlet.http.HttpServletRequest;
import java.security.SecureRandom;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.time.LocalDateTime;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
public class AuthService {
    private static final SecureRandom SECURE_RANDOM = new SecureRandom();

    private final UserAccountRepository userRepository;
    private final LoginSessionRepository sessionRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final JwtProperties jwtProperties;
    private final AuditLogService auditLogService;
    private final StringRedisTemplate redisTemplate;
    private final int verificationCodeMinutes;
    private final boolean exposeVerificationCode;

    public AuthService(
        UserAccountRepository userRepository,
        LoginSessionRepository sessionRepository,
        PasswordEncoder passwordEncoder,
        JwtService jwtService,
        JwtProperties jwtProperties,
        AuditLogService auditLogService,
        StringRedisTemplate redisTemplate,
        @Value("${app.auth.verification-code-minutes:5}") int verificationCodeMinutes,
        @Value("${app.auth.expose-verification-code:false}") boolean exposeVerificationCode
    ) {
        this.userRepository = userRepository;
        this.sessionRepository = sessionRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.jwtProperties = jwtProperties;
        this.auditLogService = auditLogService;
        this.redisTemplate = redisTemplate;
        this.verificationCodeMinutes = verificationCodeMinutes;
        this.exposeVerificationCode = exposeVerificationCode;
    }

    public AuthDtos.UserView register(AuthDtos.RegisterRequest request, HttpServletRequest servletRequest) {
        ensurePasswordStrength(request.password());
        String account = request.account().trim();
        if (userRepository.existsByAccount(account)) {
            throw new BusinessException(HttpStatus.CONFLICT, "账号已存在");
        }
        if (StringUtils.hasText(request.phone()) && userRepository.existsByPhone(request.phone().trim())) {
            throw new BusinessException(HttpStatus.CONFLICT, "手机号已存在");
        }
        if (StringUtils.hasText(request.email()) && userRepository.existsByEmail(request.email().trim())) {
            throw new BusinessException(HttpStatus.CONFLICT, "邮箱已存在");
        }

        LocalDateTime now = LocalDateTime.now();
        UserAccount user = new UserAccount();
        user.setAccount(account);
        user.setPasswordHash(passwordEncoder.encode(request.password()));
        user.setName(request.name().trim());
        user.setPhone(trimToNull(request.phone()));
        user.setEmail(trimToNull(request.email()));
        user.setOrganization(trimToNull(request.organization()));
        user.setRole("user");
        user.setPermissions(PermissionCatalog.permissionsForRole("user"));
        user.setActive(true);
        user.setCreatedAt(now);
        user.setUpdatedAt(now);
        UserAccount saved = userRepository.save(user);
        auditLogService.record("auth.register", "user_accounts", account, saved.getId(), clientIp(servletRequest));
        return AuthDtos.UserView.from(saved);
    }

    public AuthDtos.AuthResponse login(AuthDtos.LoginRequest request, HttpServletRequest servletRequest) {
        String identifier = request.account().trim();
        UserAccount user = userRepository.findFirstByAccountOrPhoneOrEmail(identifier, identifier, identifier)
            .orElseThrow(() -> new BusinessException(HttpStatus.UNAUTHORIZED, "账号或密码不正确"));
        if (!user.isActive()) {
            throw new BusinessException(HttpStatus.FORBIDDEN, "账号已停用");
        }
        if (!passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            throw new BusinessException(HttpStatus.UNAUTHORIZED, "账号或密码不正确");
        }

        LocalDateTime now = LocalDateTime.now();
        user.setLastLoginAt(now);
        user.setLastLoginIp(clientIp(servletRequest));
        user.setUpdatedAt(now);
        userRepository.save(user);

        String accessToken = jwtService.createAccessToken(user);
        String refreshToken = jwtService.createRefreshToken(user);
        LoginSession session = new LoginSession();
        session.setUserId(user.getId());
        session.setRefreshTokenHash(hashToken(refreshToken));
        session.setLoginIp(clientIp(servletRequest));
        session.setUserAgent(servletRequest.getHeader("User-Agent"));
        session.setCreatedAt(now);
        session.setExpiresAt(now.plusDays(jwtProperties.getRefreshTokenDays()));
        session.setRevoked(false);
        sessionRepository.save(session);
        auditLogService.record("auth.login", "login_sessions", user.getAccount(), user.getId(), clientIp(servletRequest));
        return new AuthDtos.AuthResponse(accessToken, refreshToken, AuthDtos.UserView.from(user));
    }

    public AuthDtos.AuthResponse refresh(String refreshToken) {
        try {
            if (!jwtService.isTokenType(refreshToken, "refresh")) {
                throw new BusinessException(HttpStatus.UNAUTHORIZED, "refreshToken 无效");
            }
            LoginSession session = sessionRepository.findByRefreshTokenHashAndRevokedFalse(hashToken(refreshToken))
                .filter(item -> item.getExpiresAt().isAfter(LocalDateTime.now()))
                .orElseThrow(() -> new BusinessException(HttpStatus.UNAUTHORIZED, "refreshToken 已失效"));
            UserAccount user = userRepository.findById(session.getUserId())
                .filter(UserAccount::isActive)
                .orElseThrow(() -> new BusinessException(HttpStatus.UNAUTHORIZED, "用户不存在或已停用"));
            return new AuthDtos.AuthResponse(jwtService.createAccessToken(user), refreshToken, AuthDtos.UserView.from(user));
        } catch (JwtException | IllegalArgumentException exception) {
            throw new BusinessException(HttpStatus.UNAUTHORIZED, "refreshToken 无效");
        }
    }

    public void logout(String refreshToken, HttpServletRequest servletRequest) {
        UserAccount user = currentUserOrNull();
        if (StringUtils.hasText(refreshToken)) {
            sessionRepository.findByRefreshTokenHashAndRevokedFalse(hashToken(refreshToken.trim())).ifPresent(session -> {
                session.setRevoked(true);
                sessionRepository.save(session);
            });
        } else if (user != null) {
            revokeUserSessions(user.getId());
        }
        auditLogService.record("auth.logout", "login_sessions", user == null ? "anonymous" : user.getAccount(), user == null ? null : user.getId(), clientIp(servletRequest));
    }

    public AuthDtos.UserView me() {
        return AuthDtos.UserView.from(requireCurrentUser());
    }

    public void changePassword(AuthDtos.ChangePasswordRequest request, HttpServletRequest servletRequest) {
        ensurePasswordStrength(request.newPassword());
        UserAccount user = requireCurrentUser();
        if (!passwordEncoder.matches(request.oldPassword(), user.getPasswordHash())) {
            throw new BusinessException(HttpStatus.BAD_REQUEST, "原密码不正确");
        }
        user.setPasswordHash(passwordEncoder.encode(request.newPassword()));
        user.setUpdatedAt(LocalDateTime.now());
        userRepository.save(user);
        revokeUserSessions(user.getId());
        auditLogService.record("auth.password.change", "user_accounts", user.getAccount(), user.getId(), clientIp(servletRequest));
    }

    public Map<String, Object> sendPasswordResetCode(AuthDtos.SendCodeRequest request, HttpServletRequest servletRequest) {
        String identifier = normalizeIdentifier(request.account());
        UserAccount user = findUserForPasswordReset(identifier);
        if (!user.isActive()) {
            throw new BusinessException(HttpStatus.FORBIDDEN, "账号已停用");
        }

        String code = String.format("%06d", SECURE_RANDOM.nextInt(1_000_000));
        String key = resetCodeKey(identifier);
        redisTemplate.opsForValue().set(key, code, Duration.ofMinutes(verificationCodeMinutes));

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("status", "sent");
        result.put("expiresInMinutes", verificationCodeMinutes);
        result.put("maskedTarget", maskTarget(identifier));
        if (exposeVerificationCode) {
            result.put("debugCode", code);
        }
        auditLogService.record("auth.password.code", "user_accounts", user.getAccount(), user.getId(), clientIp(servletRequest));
        return result;
    }

    public void resetPassword(AuthDtos.ResetPasswordRequest request, HttpServletRequest servletRequest) {
        ensurePasswordStrength(request.newPassword());
        String identifier = normalizeIdentifier(request.account());
        UserAccount user = findUserForPasswordReset(identifier);
        if (!user.isActive()) {
            throw new BusinessException(HttpStatus.FORBIDDEN, "账号已停用");
        }
        user.setPasswordHash(passwordEncoder.encode(request.newPassword()));
        user.setUpdatedAt(LocalDateTime.now());
        userRepository.save(user);
        redisTemplate.delete(resetCodeKey(identifier));
        revokeUserSessions(user.getId());
        auditLogService.record("auth.password.reset", "user_accounts", user.getAccount(), user.getId(), clientIp(servletRequest));
    }

    public UserAccount requireCurrentUser() {
        UserAccount user = currentUserOrNull();
        if (user == null) {
            throw new BusinessException(HttpStatus.UNAUTHORIZED, "请先登录");
        }
        return userRepository.findById(user.getId()).orElse(user);
    }

    public String hashToken(String token) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(token.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is not available", exception);
        }
    }

    private void revokeUserSessions(String userId) {
        List<LoginSession> sessions = sessionRepository.findByUserIdAndRevokedFalse(userId);
        sessions.forEach(session -> session.setRevoked(true));
        sessionRepository.saveAll(sessions);
    }

    private UserAccount currentUserOrNull() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication != null && authentication.getPrincipal() instanceof UserAccount user) {
            return user;
        }
        return null;
    }

    private void ensurePasswordStrength(String password) {
        if (password == null || password.length() < 6) {
            throw new BusinessException(HttpStatus.BAD_REQUEST, "密码长度至少 6 位");
        }
    }

    private UserAccount findUserForPasswordReset(String identifier) {
        return userRepository.findFirstByAccountOrPhoneOrEmail(identifier, identifier, identifier)
            .orElseThrow(() -> new BusinessException(HttpStatus.NOT_FOUND, "账号不存在"));
    }

    private String normalizeIdentifier(String identifier) {
        return identifier.trim().toLowerCase();
    }

    private String resetCodeKey(String identifier) {
        return "agri:auth:reset-code:" + hashToken(identifier);
    }

    private String maskTarget(String value) {
        if (value.contains("@")) {
            String[] parts = value.split("@", 2);
            String prefix = parts[0].length() <= 2 ? "**" : parts[0].substring(0, 2) + "***";
            return prefix + "@" + parts[1];
        }
        if (value.length() >= 7) {
            return value.substring(0, 3) + "****" + value.substring(value.length() - 4);
        }
        return value.charAt(0) + "***";
    }

    private String trimToNull(String value) {
        return StringUtils.hasText(value) ? value.trim() : null;
    }

    private String clientIp(HttpServletRequest request) {
        String forwarded = request.getHeader("X-Forwarded-For");
        if (StringUtils.hasText(forwarded)) {
            return forwarded.split(",")[0].trim();
        }
        return request.getRemoteAddr();
    }
}