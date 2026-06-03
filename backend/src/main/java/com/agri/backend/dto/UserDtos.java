package com.agri.backend.dto;

import jakarta.validation.constraints.NotBlank;

public final class UserDtos {
    private UserDtos() {
    }

    public record UpsertUserRequest(
        @NotBlank String account,
        String password,
        @NotBlank String name,
        String phone,
        String email,
        String role,
        String organization,
        Boolean active
    ) {
    }

    public record RoleChangeRequest(@NotBlank String role) {
    }

    public record StatusRequest(Boolean active) {
    }

    public record ResetPasswordRequest(String password) {
    }
}