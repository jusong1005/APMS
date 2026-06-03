package com.agri.backend.repository;

import com.agri.backend.domain.LoginSession;
import java.util.List;
import java.util.Optional;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface LoginSessionRepository extends MongoRepository<LoginSession, String> {
    Optional<LoginSession> findByRefreshTokenHashAndRevokedFalse(String refreshTokenHash);

    List<LoginSession> findByUserIdAndRevokedFalse(String userId);
}