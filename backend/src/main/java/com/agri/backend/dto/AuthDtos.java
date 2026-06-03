package com.agri.backend.dto;

import com.agri.backend.domain.UserAccount;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import java.time.LocalDateTime;
import java.util.List;

public final class AuthDtos {
    private AuthDtos() {
    }

    public record RegisterRequest(
        @NotBlank String account,
        @NotBlank String password,
        @NotBlank String name,
        String phone,
        @Email String email,
        String organization
    ) {
    }

    public record LoginRequest(@NotBlank String account, @NotBlank String password) {
    }

    public record TokenRefreshRequest(@NotBlank String refreshToken) {
    }

    public record LogoutRequest(String refreshToken) {
    }

    public record ChangePasswordRequest(@NotBlank String oldPassword, @NotBlank String newPassword) {
    }

    public record SendCodeRequest(@NotBlank String account) {
    }

    public record ResetPasswordRequest(@NotBlank String account, String code, @NotBlank String newPassword) {
    }

    public record AuthResponse(String accessToken, String refreshToken, UserView user) {
    }

    public record UserView(
        String id,
        String account,
        String name,
        String phone,
        String email,
        String role,
        String organization,
        List<String> permissions,
        boolean active,
        String avatarUrl,
        LocalDateTime createdAt,
        LocalDateTime lastLoginAt
    ) {
        public static UserView from(UserAccount user) {
            return new UserView(
                user.getId(),
                user.getAccount(),
                user.getName(),
                user.getPhone(),
                user.getEmail(),
                user.getRole(),
                user.getOrganization(),
                user.getPermissions(),
                user.isActive(),
                user.getAvatarUrl(),
                user.getCreatedAt(),
                user.getLastLoginAt()
            );
        }
    }
}