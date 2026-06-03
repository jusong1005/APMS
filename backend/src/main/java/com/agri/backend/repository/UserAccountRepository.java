package com.agri.backend.repository;

import com.agri.backend.domain.UserAccount;
import java.util.Optional;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface UserAccountRepository extends MongoRepository<UserAccount, String> {
    Optional<UserAccount> findFirstByAccountOrPhoneOrEmail(String account, String phone, String email);

    boolean existsByAccount(String account);

    boolean existsByPhone(String phone);

    boolean existsByEmail(String email);
}