package com.agri.backend.security;

import com.agri.backend.config.JwtProperties;
import com.agri.backend.domain.UserAccount;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.util.Date;
import java.util.Map;
import javax.crypto.SecretKey;
import org.springframework.stereotype.Service;

@Service
public class JwtService {
    private final JwtProperties properties;

    public JwtService(JwtProperties properties) {
        this.properties = properties;
    }

    public String createAccessToken(UserAccount user) {
        return createToken(user, "access", Duration.ofMinutes(properties.getAccessTokenMinutes()));
    }

    public String createRefreshToken(UserAccount user) {
        return createToken(user, "refresh", Duration.ofDays(properties.getRefreshTokenDays()));
    }

    public Claims parse(String token) {
        return Jwts.parser()
            .verifyWith(signingKey())
            .build()
            .parseSignedClaims(token)
            .getPayload();
    }

    public boolean isTokenType(String token, String type) {
        Object value = parse(token).get("type");
        return type.equals(value);
    }

    private String createToken(UserAccount user, String type, Duration ttl) {
        Instant now = Instant.now();
        return Jwts.builder()
            .claims(Map.of("account", user.getAccount(), "role", PermissionCatalog.normalizeRole(user.getRole()), "type", type))
            .subject(user.getId())
            .issuedAt(Date.from(now))
            .expiration(Date.from(now.plus(ttl)))
            .signWith(signingKey(), Jwts.SIG.HS256)
            .compact();
    }

    private SecretKey signingKey() {
        byte[] bytes = properties.getSecret().getBytes(StandardCharsets.UTF_8);
        return Keys.hmacShaKeyFor(bytes);
    }
}